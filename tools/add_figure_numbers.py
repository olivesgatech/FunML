#!/usr/bin/env python3
"""Add Figure N.M: prefix to all top-level \\caption{} commands in LaTeX lecture files.

Rules:
- Only processes files that have \\lecture{N} to get the lecture number.
- Counts every \\begin{figure} (or figure*) to keep numbering aligned with LaTeX.
- A caption is "top-level" if it is not inside a subfigure or minipage block.
- If a figure has exactly ONE caption total (even if layout-wrapped in a minipage),
  that one caption is treated as the top-level figure caption.
- If a figure has multiple captions all inside sub-containers, they are sub-captions
  and are left untouched (no outer figure caption to label).
- Idempotent: captions already starting with "Figure N.M:" are not double-prefixed.
- Skips figures that appear inside LaTeX comment lines (lines starting with %).
"""

import re
import sys
from pathlib import Path


def _build_comment_mask(tex: str) -> list:
    """Return bool list: True where the character is inside a LaTeX comment."""
    mask = [False] * len(tex)
    in_comment = False
    i = 0
    while i < len(tex):
        c = tex[i]
        if c == "\n":
            in_comment = False
            mask[i] = False
            i += 1
        elif c == "\\" and not in_comment:
            # Escaped character — mark both chars as not-comment, skip next.
            mask[i] = False
            i += 1
            if i < len(tex):
                mask[i] = False
                i += 1
        elif c == "%" and not in_comment:
            in_comment = True
            mask[i] = True
            i += 1
        else:
            mask[i] = in_comment
            i += 1
    return mask


def _find_env_positions(tex: str, comment_mask: list, env_name: str):
    """Find (start, end) positions of \\begin{env}...\\end{env}, skipping commented ones."""
    begin_pat = re.compile(r"\\begin\{" + re.escape(env_name) + r"[^}]*\}")
    end_pat = re.compile(r"\\end\{" + re.escape(env_name) + r"\}")

    begins = [m for m in begin_pat.finditer(tex) if not comment_mask[m.start()]]
    ends = [m for m in end_pat.finditer(tex) if not comment_mask[m.start()]]

    pairs = []
    ei = 0
    depth = 0
    for bm in begins:
        if depth == 0:
            start = bm.start()
        depth += 1
        # find the matching end
        while ei < len(ends) and ends[ei].start() < bm.start():
            ei += 1
        if ei < len(ends):
            pairs.append((bm.start(), bm.end(), ends[ei].start(), ends[ei].end()))
    return pairs


def _find_figure_blocks(tex: str, comment_mask: list):
    """Yield (fig_begin_end, fig_content_start, fig_content_end) for each figure."""
    begin_pat = re.compile(r"\\begin\{figure\*?\}")
    end_pat = re.compile(r"\\end\{figure\*?\}")

    begins = [m for m in begin_pat.finditer(tex) if not comment_mask[m.start()]]
    ends_all = [m for m in end_pat.finditer(tex) if not comment_mask[m.start()]]

    ei = 0
    for bm in begins:
        # advance ends pointer past this begin
        while ei < len(ends_all) and ends_all[ei].start() < bm.end():
            ei += 1
        if ei >= len(ends_all):
            break
        em = ends_all[ei]
        yield bm.start(), bm.end(), em.start(), em.end()
        ei += 1


def _in_any_range(pos, ranges):
    return any(s <= pos < e for s, e in ranges)


def _find_sub_ranges(fig_content: str, env_name: str):
    """Find all begin/end ranges of env_name inside fig_content (no comment awareness needed)."""
    begin_pat = re.compile(r"\\begin\{" + re.escape(env_name) + r"[^}]*\}")
    end_pat = re.compile(r"\\end\{" + re.escape(env_name) + r"\}")

    ranges = []
    pos = 0
    for bm in begin_pat.finditer(fig_content):
        em = end_pat.search(fig_content, bm.end())
        if em:
            ranges.append((bm.start(), em.end()))
    return ranges


def add_figure_numbers_to_tex(tex_path: Path, dry_run: bool = False) -> int:
    """Modify tex_path in-place. Returns number of captions modified."""
    tex = tex_path.read_text(errors="ignore")

    lec_match = re.search(r"\\lecture\{(\d+)\}", tex)
    if not lec_match:
        return 0
    lec_num = lec_match.group(1)

    comment_mask = _build_comment_mask(tex)
    cap_pat = re.compile(r"\\caption\{")

    # Collect (insert_position, prefix) in order, then apply in reverse.
    insertions = []
    fig_count = 0

    for b_start, b_end, e_start, e_end in _find_figure_blocks(tex, comment_mask):
        fig_count += 1
        fig_content = tex[b_end:e_start]  # content between \begin{figure} and \end{figure}

        sub_ranges = _find_sub_ranges(fig_content, "subfigure")
        mini_ranges = _find_sub_ranges(fig_content, "minipage")
        inner_ranges = sub_ranges + mini_ranges

        all_caps = list(cap_pat.finditer(fig_content))
        if not all_caps:
            continue

        top_level = [m for m in all_caps if not _in_any_range(m.start(), inner_ranges)]

        if top_level:
            targets = top_level
        elif len(all_caps) == 1:
            # Single caption in a layout wrapper — treat as the figure caption.
            targets = all_caps
        else:
            # Multiple sub-captions only — skip.
            continue

        prefix = f"Figure {lec_num}.{fig_count}: "
        for m in targets:
            insert_pos = b_end + m.end()  # absolute position in original tex
            rest = tex[insert_pos:]
            if re.match(r"Figure\s+\d+\.\d+\s*:", rest):
                continue  # idempotent
            insertions.append((insert_pos, prefix))

    if not insertions:
        return 0

    # Apply in reverse order so earlier positions stay valid.
    insertions.sort(key=lambda x: x[0], reverse=True)
    tex_list = list(tex)
    for pos, prefix in insertions:
        tex_list[pos:pos] = list(prefix)

    new_tex = "".join(tex_list)
    if not dry_run:
        tex_path.write_text(new_tex)

    return len(insertions)


def main():
    dry_run = "--dry-run" in sys.argv
    lectures_dir = Path(__file__).resolve().parent.parent / "lectures"
    tex_files = sorted(lectures_dir.glob("*.tex"))

    total_files = 0
    total_caps = 0
    for tex_path in tex_files:
        n = add_figure_numbers_to_tex(tex_path, dry_run=dry_run)
        if n:
            total_files += 1
            total_caps += n
            flag = " (dry-run)" if dry_run else ""
            print(f"  {tex_path.name}: {n} caption(s) updated{flag}")

    print(f"\nDone: {total_caps} caption(s) across {total_files} file(s).")


if __name__ == "__main__":
    main()
