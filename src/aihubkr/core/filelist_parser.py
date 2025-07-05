import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List, Optional, Tuple


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
        parent: Optional["Node"] = None
        children: List["Node"] = field(default_factory=list)
        depth: int = 0

        def to_dict(self):
            """
            Convert the tree under the current node to a dict mapping paths to lists
            of children.
            """
            if len(self.children) == 0:
                return str(self.path)
            return {
                f"[{self.file_key}] " if self.file_key is not None else "" +
                f"{self.path}" +
                f" ({sizeof_fmt(self.file_display_size)})" if self.file_max_possible_size is not None else "": [child.to_dict() for child in self.children]
            }

        lru_cache()

        def full_path(self):
            """
            Get the full path for the node.
            """
            if self.parent is None:
                return self.path
            return self.parent.full_path() / self.path

    def parse_tree_output(self, body: str) -> Tuple[Node, List[Path]]:
        """
        Parse the output of the linux `tree` command stored in `tree_path` and
        return a `Node` representing the parsed tree and a list of paths.
        """
        paths = []

        try:
            body_lines = body.splitlines()

            # Assume the root directory is on the first line
            root = body_lines[0].replace("└─", "").strip()
            tree = parent = node = AIHubResponseParser.Node(path=Path(root))

            # Parse lines one by one
            for idx, line in enumerate(body_lines[1:]):
                # Split the tree formatting prefix and the path for lines like:
                # │   │       │   ├── 1.51.51.5_rotated.4dfp.ifh
                # Note: This regex handles the expected format, but may need updates for edge cases
                match = re.match("(.*?─+ ?)(.*)", line)
                if match is None:
                    continue

                prefix, path = match.groups()

                # Deteministic leaf node
                file_display_size = None
                file_min_possible_size = None
                file_max_possible_size = None
                file_key = None
                if " | " in path:
                    data_match = re.match(r"(.*) \| (\d+ [KMGT]?B) \| (\d+)", path)
                    if data_match is None:
                        continue
                    path, size_iec, file_key = data_match.groups()

                    size_match = re.match(r"(\d+) ([KMGT]?)B", size_iec)
                    if size_match is None:
                        continue
                    size, unit = size_match.groups()

                    # Assume size because we don't know this result is round up or floor.
                    file_display_size = int((int(size)) * 1024 ** (" KMGT".index(unit)))
                    file_min_possible_size = int((int(size) - 0.5) * 1024 ** (" KMGT".index(unit)))
                    file_max_possible_size = int((int(size) + 1.0) * 1024 ** (" KMGT".index(unit)))

                path = Path(path.strip())

                if "├─" in prefix:
                    idx = prefix.rfind("├─")
                    if len(prefix) - 2 != idx:
                        continue
                    prefix_len = idx
                elif "└─" in prefix:
                    idx = prefix.rfind("└─")
                    if len(prefix) - 2 != idx:
                        continue
                    prefix_len = idx
                else:
                    continue

                # Remove heading empty spaces
                # which occurs in every line
                depth = 1
                prefix_len -= 8

                if prefix_len > 0:
                    # depth >= 2
                    while prefix_len > 0:
                        if depth == 1:
                            # Only depth 2 has 3 spaces
                            depth += 1
                            prefix_len -= 3
                        else:
                            depth += 1
                            prefix_len -= 4

                # Determine nesting level relative to previous node
                if depth > node.depth:
                    parent = node
                elif depth < node.depth:
                    for _ in range(depth, node.depth):
                        parent = parent.parent

                # Append to tree at the appropriate level
                node = AIHubResponseParser.Node(path, parent=parent, depth=depth)
                if file_key is not None:
                    node.file_display_size = file_display_size
                    node.file_min_possible_size = file_min_possible_size
                    node.file_max_possible_size = file_max_possible_size
                    node.file_key = file_key
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
