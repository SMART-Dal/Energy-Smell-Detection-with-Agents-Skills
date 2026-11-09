You are a performance testing expert. You will write the inputs for an energy measurement of one Python function from a real repository. We run the original function and a modified version of it on your inputs, each input many times in a row, and compare their energy use and their outputs.

# What to write
Python source defining two functions, `checks()` and `cases()`. Each returns a list of `(label, thunk)` pairs with distinct labels. A thunk takes no arguments and returns a tuple of positional arguments for the function, e.g. `lambda: (rows, 3)`. For keyword arguments the thunk returns `call(...)`, e.g. `lambda: call(rows, sep=",")`; `call` is provided, do not import or define it. A method is called as a plain function: the thunk builds the instance and passes it as the first argument (a classmethod gets its class there, a staticmethod nothing; the task says which).
**The thunk returns the arguments; it never calls the function under test.** We call the function with them, and time only that call.

# Instructions
1. **Setup is never timed**: everything that builds data, objects or files goes in the thunk or in module-level code. Thunks run before the timing starts; only the call of the function is timed.

2. **`cases()`: exactly 8 measured inputs.** We run them on the original function and keep the 4 that do the most work.
    - Define a real workload: the kind of data this function gets in this repository (see where the repository calls it). Use realistic scale and complexity, and a fixed random seed (`random.Random(0)`) when generating data.
    - Generate stressful inputs: complex, time-consuming, as diverse as possible. Each case should make the function do substantial and different work: different paths through its code, sizes, data distributions, hit and miss ratios, duplicates, lengths.
    - Avoid uniformity or patterns (repeating, sorted, same values) that a simple trick could exploit, unless that pattern is what the repository really passes.
    - One call should take roughly 1 ms to 200 ms on the original. Inputs where one call takes over 1 s are dropped. Keep the data in memory under about 100 MB, and building all inputs under about 10 s.
    - The function's output is compared in full after every input, so keep what it returns (and anything it writes) under about 100 000 values. Its arguments are rendered before and after each call to see whether it changed them, so keep each input's data under about 1 000 000 values.
    - Every case must run to completion on the original function without raising.

3. **`checks()`: 2 or 3 small edge inputs** (empty, one element, None, an odd type) checked only for identical behaviour, never measured. These may raise.

4. **Build real inputs; never replace code.** No mocks, no monkeypatching, no `unittest.mock`, no assigning functions or lambdas to attributes, and no subclass that overrides a method of a repository or library class -- a subclass whose `get` returns canned data instead of making the request is a mock too. Setting data (a module's configuration, an object's fields) to build an input is fine. No network access, no subprocesses. Do not fake the environment either: no stand-in programs on `PATH`, no fake system files.
    - Module globals the function reads must be set on the repository's own module (`import pricing; pricing.args = ...`, `hyperlink.slugs.update(...)`); a variable of the same name in your source is a different variable and the function never sees it.
    - Prepare the way the repository's own callers do: if a caller runs some setup before calling the function (adds a path, loads a config), do the same in the thunk.

5. **Files**: if the function reads files, create them under `WORKDIR` (a provided `pathlib.Path`; do not define it), in module-level code or in the thunk. Anything the function writes must go under `WORKDIR` too.

6. **Same work on every call**: the call is repeated many times, and every call gets the arguments of its own thunk call, all built and kept in memory before the timing starts. So keep a thunk cheap next to one call: build large data once, in module-level code, and have the thunk return it -- or a copy (`list(data)`, `dict(data)`) if the function changes it (adds to a dict, sorts or fills a list in place). Anything the function changes outside its arguments (a class attribute, a module global, a cache, a file) carries over from one call to the next, so if it caches or records what it has seen, give every thunk call new keys (e.g. with `itertools.count()`), so every call takes the same path. If it creates files, have the thunk remove them first. No time-dependent or unseeded random behaviour.

7. Import the repository's modules exactly as shown in the task. Use only the standard library, the repository itself and packages the repository already imports. Everything you can know about the repository is in the task: do not try to recall its code from memory, and build the inputs from the classes and functions shown there.

8. **If the function cannot run here at all** -- it needs network access, a remote service, credentials, special hardware, or a library that is not available -- and no input could avoid that, do not write code: reply with one line `CANNOT RUN: <the reason>`. A function whose work starts with a request to a server (an HTTP client's `get`, a database query) cannot run here, even if the rest of it only processes the answer.

Decide on the inputs and write the code: simple inputs that run are better than clever ones that do not.

# Output format
Exactly one ```python block holding the complete source. An example for a function `summarize(rows, top=10)`:
```python
import random

def _rows(n, columns, seed):
    rng = random.Random(seed)
    return [{f"c{j}": rng.randint(0, 10**6) for j in range(columns)} for _ in range(n)]

def checks():
    return [
        ("empty",      lambda: ([],)),                            # summarize([])
        ("none-value", lambda: ([{"c0": None}],)),
    ]

def cases():
    return [
        ("typical",    lambda: (_rows(2_000, 4, 0),)),            # summarize(rows)
        ("top-100",    lambda: call(_rows(5_000, 4, 1), top=100)), # summarize(rows, top=100)
        # ... 8 in total
    ]
```
A second example, for a method `Index.lookup(self, words)` of `search/index.py`. The instance is built in the thunk and passed first; the vocabulary file it reads is created under `WORKDIR`; a module setting it reads is set on the repository's own module; and because it records the words it has seen in `self.seen`, every thunk call gets words of its own, so that every call takes the same path:
```python
import itertools
import random
import search.index
from search.index import Index

search.index.CASE_SENSITIVE = False                  # a setting the method reads: data, set on its module
_VOCAB = WORKDIR / "vocab.txt"                       # a file it reads
_VOCAB.write_text("\n".join(f"w{i}" for i in range(50_000)))
_batch = itertools.count()

def _words(n, hit_ratio, seed):
    rng = random.Random(seed)
    b = next(_batch)                                 # fresh misses for every thunk call
    return [f"w{rng.randrange(50_000)}" if rng.random() < hit_ratio else f"x{b}_{i}"
            for i in range(n)]

def checks():
    return [("no-words", lambda: (Index(_VOCAB), []))]

def cases():
    return [
        ("mostly-hits",   lambda: (Index(_VOCAB), _words(20_000, 0.9, 0))),
        ("mostly-misses", lambda: (Index(_VOCAB), _words(20_000, 0.1, 1))),
        # ... 8 in total
    ]
```


=== USER ===

Repository: sample-apps
Function under test: `perform_cross_validation` in `rag-blueprint/eval/train_logistic_regression.py`
Import it as `from train_logistic_regression import perform_cross_validation`.

## The function
```python
def perform_cross_validation(file_path, output_coef_file):
    """Loads data, applies standardization, and performs 5-fold stratified cross-validation."""
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        logging.error(f"Input file '{file_path}' not found.")
        raise FileNotFoundError(f"Input file '{file_path}' not found.")

    # Define and drop irrelevant columns
    columns_to_drop = [
        "doc_id",
        "query_id",
        "relevance_score",
    ]
    df = df.drop(columns=columns_to_drop)
    # Convert target variable to binary (0/1)
    df["relevance_label"] = df["relevance_label"].astype(int)

    # Define features (X) and target (y)
    X = df.drop(columns=["relevance_label"])
    features = X.columns.tolist()  # Store feature names for later use
    y = df["relevance_label"]

    # Display feature statistics before scaling
    print("\nFeature Statistics (before scaling):")
    print("-" * 60)
    print(f"{'Feature':<35} | {'Mean':<10} | {'Std':<10} | {'Min':<10} | {'Max':<10}")
    print("-" * 60)
    for feature in features:
        stats = X[feature].describe()
        print(
            f"{feature:<35} | {stats['mean']:<10.4f} | {stats['std']:<10.4f} | {stats['min']:<10.4f} | {stats['max']:<10.4f}"
        )
    print("-" * 60)

    # Initialize StandardScaler
    scaler = StandardScaler()

    # --- Stratified K-Fold Cross-Validation ---
    N_SPLITS = 5
    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=42)
    model = LogisticRegression(random_state=42)

    # Lists to store metrics for each fold
    accuracies, precisions, recalls, f1_scores = [], [], [], []
    log_losses, roc_aucs, avg_precisions = [], [], []

    logging.info(
        f"Performing {N_SPLITS}-Fold Stratified Cross-Validation with standardization...\n"
    )

    for fold, (train_index, test_index) in enumerate(skf.split(X, y), 1):
        # Split the data for the current fold
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]

        # Fit scaler on training data and transform both train and test
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Train the model on scaled data
        model.fit(X_train_scaled, y_train)

        # Make predictions on scaled test data
        y_pred = model.predict(X_test_scaled)
        y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]

        # Calculate and store metrics
        accuracies.append(accuracy_score(y_test, y_pred))
        precisions.append(precision_score(y_test, y_pred, zero_division=0))
        recalls.append(recall_score(y_test, y_pred, zero_division=0))
        f1_scores.append(f1_score(y_test, y_pred, zero_division=0))
        log_losses.append(log_loss(y_test, y_pred_proba))
        roc_aucs.append(roc_auc_score(y_test, y_pred_proba))
        avg_precisions.append(average_precision_score(y_test, y_pred_proba))

        logging.info(
            f"Fold {fold}: Acc = {accuracies[-1]:.4f}, F1 = {f1_scores[-1]:.4f}, ROC AUC = {roc_aucs[-1]:.4f}, Avg Prec = {avg_precisions[-1]:.4f}"
        )

    # --- Output Results ---
    print("\n" + "-" * 60)
    print(f"{'Cross-Validation Results (5-Fold, Standardized)':^60}")
    print("-" * 60)
    print(f"{'Metric':<18} | {'Mean':<18} | {'Std Dev':<18}")
    print("-" * 60)
    print(
        f"{'Accuracy':<18} | {np.mean(accuracies):<18.4f} | {np.std(accuracies):<18.4f}"
    )
    print(
        f"{'Precision':<18} | {np.mean(precisions):<18.4f} | {np.std(precisions):<18.4f}"
    )
    print(f"{'Recall':<18} | {np.mean(recalls):<18.4f} | {np.std(recalls):<18.4f}")
    print(
        f"{'F1-Score':<18} | {np.mean(f1_scores):<18.4f} | {np.std(f1_scores):<18.4f}"
    )
    print(
        f"{'Log Loss':<18} | {np.mean(log_losses):<18.4f} | {np.std(log_losses):<18.4f}"
    )
    print(f"{'ROC AUC':<18} | {np.mean(roc_aucs):<18.4f} | {np.std(roc_aucs):<18.4f}")
    print(
        f"{'Avg Precision':<18} | {np.mean(avg_precisions):<18.4f} | {np.std(avg_precisions):<18.4f}"
    )
    print("-" * 60)

    # --- Model Coefficients ---
    # Retrain on full standardized data to get final coefficients
    X_scaled = scaler.fit_transform(X)
    model.fit(X_scaled, y)

    print("\nModel Coefficients (on standardized features):")
    print("-" * 50)
    for feature, coef in zip(features, model.coef_[0]):
        print(f"{feature:<35}: {coef:.6f}")
    print(f"{'Intercept':<35}: {model.intercept_[0]:.6f}")
    print("-" * 50)

    # Show transformed coefficients for original features
    transformed_coefs = model.coef_[0] / scaler.scale_
    transformed_intercept = model.intercept_[0] - np.sum(
        model.coef_[0] * scaler.mean_ / scaler.scale_
    )

    print("\nTransformed Coefficients (for original unscaled features):")
    print("-" * 50)
    for feature, coef in zip(features, transformed_coefs):
        print(f"{feature:<35}: {coef:.6f}")
    print(f"{'Intercept':<35}: {transformed_intercept:.6f}")
    print("-" * 50)

    # Save coefficients expression to file
    if output_coef_file:
        save_coefficients_expression(
            model, features, model.intercept_[0], scaler, output_coef_file
        )
```

## Imports of its module
```python
import argparse
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    log_loss,
    roc_auc_score,
    average_precision_score,
)
import logging
import os
import json
```

## Definitions it uses from the same module
```python
def save_coefficients_expression(model, features, intercept, scaler, output_file_path):
    """Saves the model coefficients as a linear expression that accounts for standardization."""
    try:
        # Transform coefficients to work with original (unscaled) features
        # For standardized features: z = (x - mean) / std
        # So the original expression: coef * z + intercept
        # Becomes: (coef / std) * x + (intercept - coef * mean / std)

        transformed_coefs = model.coef_[0] / scaler.scale_
        transformed_intercept = intercept - np.sum(
            model.coef_[0] * scaler.mean_ / scaler.scale_
        )

        # Create expression for original (unscaled) features
        expression_parts = [f"{transformed_intercept:.6f}"]
        for feature, coef in zip(features, transformed_coefs):
            expression_parts.append(f"{coef:+.6f}*{feature}")

        expression = "".join(expression_parts)

        # Also save scaling parameters for reference
        scaling_info = {
            "feature_means": dict(zip(features, scaler.mean_)),
            "feature_stds": dict(zip(features, scaler.scale_)),
            "original_coefficients": dict(zip(features, model.coef_[0])),
            "original_intercept": float(intercept),
            "transformed_coefficients": dict(zip(features, transformed_coefs)),
            "transformed_intercept": float(transformed_intercept),
        }

        # Save the expression
        with open(output_file_path, "w") as f:
            f.write("# Linear expression for original (unscaled) features:\n")
            f.write(expression + "\n\n")
            f.write("# Scaling and coefficient information:\n")
            f.write(json.dumps(scaling_info, indent=2))

        logging.info(f"Model coefficients expression saved to {output_file_path}")
        logging.info(
            "Expression works with original feature values (no scaling needed)"
        )

    except Exception as e:
        logging.error(f"Error saving coefficients expression: {e}")
```

## Where the repository calls it or builds its class
```python
# rag-blueprint/eval/train_logistic_regression.py:236
        base_name = os.path.splitext(os.path.basename(args.input_file))[0]
        output_coef_file_path = f"{base_name}_logreg_coefficients.txt"

    # Run the cross-validation process
    perform_cross_validation(args.input_file, output_coef_file_path)
```

Write `checks()` and `cases()` for `perform_cross_validation`. Remember: setup in the thunk or at module level, never timed.