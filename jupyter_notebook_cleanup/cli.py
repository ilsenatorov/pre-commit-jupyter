import argparse
import copy
import difflib
import json
import os
import shutil
import tempfile
import uuid
from collections import OrderedDict


class JupyterNotebookCleanup:
    @staticmethod
    def parse_args():
        psr = argparse.ArgumentParser()
        psr.add_argument("files", nargs="*", help="ipynb files")
        psr.add_argument("--dry-run", action="store_true", default=False)
        psr.add_argument("--remove-kernel-metadata", action="store_true", default=False)
        psr.add_argument("--remove-cell-metadata", action="store_true", default=False)
        psr.add_argument("--pin-patterns", default="[pin]", nargs="+")
        return psr.parse_args()

    def __init__(
        self,
        files: list,
        pin_patterns: list,
        dry_run: bool = False,
        remove_kernel_metadata: bool = False,
        remove_cell_metadata: bool = False,
    ):
        self.files = files
        self.pin_patterns = pin_patterns
        self.remove_kernel_metadata = remove_kernel_metadata
        self.remove_cell_metadata = remove_cell_metadata
        self.dry_run = dry_run

    def check_if_unremovable(self, source) -> bool:
        """comment annotation must be the first line and started with #"""
        for s in source:
            ss = s.strip()
            if ss.startswith("#") and any(x in ss for x in self.pin_patterns):
                return True
        return False

    def remove_output_file(self, path):
        """If preview=True, Do not overwrite a path, only display an diffs"""
        dump_args = {"ensure_ascii": False, "separators": (",", ": "), "indent": 1}
        # to preserve timestamps, making temporal copy
        with tempfile.TemporaryDirectory() as tdir:
            tpath = os.path.join(tdir, "jupyter-notebook-cleanup-" + str(uuid.uuid1()))
            shutil.copy2(path, tpath)
            with open(path, "rt", encoding="utf-8") as f:
                data = json.load(f, object_pairs_hook=OrderedDict)
            new_data = self.remove_output_object(data)
            before_j = json.dumps(data, **dump_args)
            after_j = json.dumps(new_data, **dump_args)
            # ensure eof newlines
            before_j = before_j.rstrip("\n") + "\n"
            after_j = after_j.rstrip("\n") + "\n"
            if self.dry_run:
                before_l, after_l = before_j.splitlines(), after_j.splitlines()
                print("\n".join(difflib.unified_diff(before_l, after_l, fromfile="before", tofile="after")))
            elif before_j != after_j:  # overwrite to the original file
                with open(path, "wt", encoding="utf-8") as fo:
                    fo.write(after_j)
            shutil.copystat(tpath, path)  # copy original timestamps

    def remove_output_object(self, data: dict) -> dict:
        """Parse the dict of data"""
        new_data = copy.deepcopy(data)
        if self.remove_kernel_metadata:
            kernelspec = new_data.get("metadata", {}).get("kernelspec", {})
            if "display_name" in kernelspec:
                kernelspec["display_name"] = ""
            if "name" in kernelspec:
                kernelspec["name"] = ""
        for cell in new_data["cells"]:
            if self.remove_cell_metadata and "metadata" in cell:
                cell["metadata"] = {}
            if "execution_count" in cell:
                cell["execution_count"] = None
            if "outputs" in cell and "source" in cell:
                source = cell["source"]
                if not isinstance(source, list):
                    continue
                if self.check_if_unremovable(source):
                    continue
                cell["outputs"] = []
        return new_data

    def run(self):
        """Run pipeline for all files"""
        for path in self.files:
            self.remove_output_file(path)


if __name__ == "__main__":
    args = JupyterNotebookCleanup.parse_args()
    jnc = JupyterNotebookCleanup(**vars(args))
    jnc.run()
