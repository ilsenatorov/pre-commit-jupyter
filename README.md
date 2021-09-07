# Jupyter pre-commit

pre-commit hook to remove cell output of .ipynb notebook and some metadata for better security.

Sample config:

```yaml
repos:
  - repo: https://github.com/roy-ht/pre-commit-jupyter
    rev: v1.3.1
    hooks:
      - id: jupyter-notebook-cleanup
        args: [--remove-kernel-metadata, --remove-cell-metadata]
```

If you have "pin patterns", You can keep cell outputs like that:

```python

# [pin]
some_function()
print("some info")
```

```python
# [donotremove]
some_function()
print("some info")
```
