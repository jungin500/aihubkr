import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple, Union


def sizeof_fmt(num, suffix="B", ignore_float=False):
    for unit in ("", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"):
        if abs(num) < 1024.0:
            if ignore_float:
                return f"{int(num)}{unit}{suffix}"
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


class AIHubResponseParser:
    @dataclass
    class Node:
        """
        A node of a directory tree with references to parent and children as well as
        the path and depth.
        """
        path: Optional[Path] = None
        file_display_size: Optional[int] = None
        file_min_possible_size: Optional[int] = None
        file_max_possible_size: Optional[int] = None
        file_key: Optional[str] = None
        parent: Optional["AIHubResponseParser.Node"] = None
        children: List["AIHubResponseParser.Node"] = field(default_factory=list)
        depth: int = 0

        def to_dict(self) -> Union[str, dict]:
            if len(self.children) == 0:
                # File node
                if self.file_key is not None and self.file_display_size is not None:
                    return f"[{self.file_key}] {self.path} ({sizeof_fmt(self.file_display_size)})"
                else:
                    return str(self.path)
            # Directory node
            return {str(self.path): [child.to_dict() for child in self.children]}

        def full_path(self) -> Path:
            """
            Get the full path for the node.
            """
            if self.parent is None:
                return self.path or Path(".")
            parent_path = self.parent.full_path()
            return parent_path / (self.path or Path("."))

    def parse_tree_output(self, body: str) -> Tuple[Optional[Node],
                                                    Optional[List[Tuple[str, bool, Optional[str],
                                                                        Optional[Tuple[int, int, int]]]]]]:
        """
        Parse the output of the linux `tree` command stored in `tree_path` and
        return a `Node` representing the parsed tree and a list of paths.
        """
        paths = []

        try:
            body_lines = body.splitlines()

            # Find the first line that contains the dataset name (skip UTF-8 headers and tree chars)
            root_line = None
            for line in body_lines:
                if (not line.startswith("The contents are encoded") and
                    not line.startswith("If the following contents") and
                    not line.startswith("Please modify the character") and
                    not line.startswith("=================") and
                    not line.startswith("==========================================") and
                    not line.strip().lower().startswith("utf-8") and
                    not line.strip().lower().startswith("output normally") and
                    not line.strip().lower().startswith("modify the character information") and
                        line.strip() != ""):
                    root_line = line
                    break
            if root_line is None:
                # Fallback to first line
                root_line = body_lines[0]

            # Clean up the root line by removing tree characters
            root = root_line.strip()
            # Remove tree characters from the beginning of the line
            root = re.sub(r'^[└├│─\s]+', '', root)
            tree = parent = node = AIHubResponseParser.Node(path=Path(root))
            # Always include the root node in paths
            paths.append((str(tree.path), False, None, None))

            # Parse lines one by one
            for idx, line in enumerate(body_lines[1:]):
                # Skip header lines and notice sections
                if (line.startswith("The contents are encoded") or
                    line.startswith("If the following contents") or
                    line.startswith("Please modify the character") or
                    line.startswith("=================") or
                    line.startswith("==========================================") or
                    line.strip().lower().startswith("utf-8") or
                    line.strip().lower().startswith("output normally") or
                    line.strip().lower().startswith("modify the character information") or
                        line.strip() == ""):
                    continue
                # Split the tree formatting prefix and the path for lines like:
                # │   │       │   ├─ filename.zip | 11 MB | 69412
                # │   │       │   ├── filename.zip | 11 MB | 69412 (test format)
                # Updated regex to handle additional dashes after tree characters
                match = re.match(r"(.*?)(└─+|├─+)\s*(.*)", line)
                if match is None:
                    continue
                prefix, tree_char, path = match.groups()
                # Deteministic leaf node
                file_display_size = None
                file_min_possible_size = None
                file_max_possible_size = None
                file_key = None
                if "|" in path:
                    # Updated regex: allow optional spaces around | and between number/unit
                    data_match = re.match(r"(.*)\s*\|\s*(\d+(?:\.\d+)?\s*[KMGT]?B)\s*\|\s*(\d+)", path)
                    if data_match is None:
                        continue
                    path, size_iec, file_key = data_match.groups()
                    size_match = re.match(r"(\d+(?:\.\d+)?)\s*([KMGT]?)B", size_iec)
                    if size_match is None:
                        continue
                    size, unit = size_match.groups()
                    size = float(size)
                    file_display_size = int(size * 1024 ** (" KMGT".index(unit)))
                    file_min_possible_size = int((size - 0.5) * 1024 ** (" KMGT".index(unit)))
                    file_max_possible_size = int((size + 1.0) * 1024 ** (" KMGT".index(unit)))
                path = Path(path.strip())
                prefix_len = len(prefix)
                # Calculate depth based on prefix length
                depth = 1
                leading_spaces = len(prefix) - len(prefix.lstrip())
                if leading_spaces > 0:
                    depth = (leading_spaces // 4) + 1
                # Determine nesting level relative to previous node
                if depth > node.depth:
                    parent = node
                elif depth < node.depth:
                    for _ in range(depth, node.depth):
                        if parent and parent.parent:
                            parent = parent.parent
                # Append to tree at the appropriate level
                node = AIHubResponseParser.Node(path, parent=parent, depth=depth)
                if file_key is not None:
                    node.file_display_size = file_display_size
                    node.file_min_possible_size = file_min_possible_size
                    node.file_max_possible_size = file_max_possible_size
                    node.file_key = file_key
                if parent:
                    parent.children.append(node)
                # Append full path to list
                if file_key is not None:
                    paths.append((str(node.full_path()), True, file_key,
                                  (file_display_size, file_min_possible_size, file_max_possible_size)))
                else:
                    paths.append((str(node.full_path()), False, None, None))
            return tree, paths
        except Exception as e:
            return None, None
