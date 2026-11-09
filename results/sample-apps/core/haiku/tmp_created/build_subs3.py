import json
subs = []
PO = '''def process_orders(
    output_dir: Path, eval_sets: list[str], full: bool = False, limit: int = 10
) -> None:
    """Process order data and aggregate products into arrays."""
    print(f"Processing orders for eval_set(s): {', '.join(eval_sets)}...")

    df_order = pd.read_csv("dataset/orders.csv")

    for eval_set in eval_sets:
        # Filter orders by eval_set
        df_order_filtered = df_order[df_order["eval_set"] == eval_set].copy()

        if len(df_order_filtered) == 0:
            print(f"⚠ No orders found for eval_set '{eval_set}', skipping...")
            continue

        # Read the corresponding order_products file
        order_products_file = f"dataset/order_products__{eval_set}.csv"
        try:
            df_order_products = pd.read_csv(order_products_file)
        except FileNotFoundError:
            print(f"⚠ File not found: {order_products_file}, skipping {eval_set}...")
            continue

        # Sort order_products by add_to_cart_order to maintain the order
        df_order_products_sorted = df_order_products.sort_values(
            ["order_id", "add_to_cart_order"]
        )

        # Group by order_id and aggregate product_ids into an array
        df_products_aggregated = (
            df_order_products_sorted.groupby("order_id")
            .agg({"product_id": lambda x: list(x)})
            .reset_index()
        )

        # Rename the column to match Vespa schema
        df_products_aggregated.rename(
            columns={"product_id": "product_ids"}, inplace=True
        )

        # Merge with orders dataframe
        df_orders_merged = df_order_filtered.merge(
            df_products_aggregated, on="order_id", how="left"
        )

        # Select only the fields needed for Vespa
        df_orders_vespa = df_orders_merged[
            [
                "order_id",
                "user_id",
                "order_dow",
                "order_hour_of_day",
                "days_since_prior_order",
                "product_ids",
            ]
        ]

        # Write to JSONL in Vespa format
        output_file = output_dir / f"orders_{eval_set}.jsonl"

        with open(output_file, "w") as f:
            for i, (_, order) in enumerate(df_orders_vespa.iterrows()):
                doc = {
                    "put": f"id:orders:order::{order['order_id']}",
                    "fields": {
                        "order_id": int(order["order_id"]),
                        "user_id": int(order["user_id"]),
                        "order_dow": int(order["order_dow"]),
                        "order_hour_of_day": int(order["order_hour_of_day"]),
                        "days_since_prior_order": (
                            float(order["days_since_prior_order"])
                            if pd.notna(order["days_since_prior_order"])
                            else None
                        ),
                        "product_ids": order["product_ids"],
                    },
                }
                f.write(json.dumps(doc) + "\\n")

                if not full and i >= limit - 1:
                    break'''

# repair b: sample mode aggregates only the orders that will be written
B = PO.replace('''        except FileNotFoundError:
            print(f"⚠ File not found: {order_products_file}, skipping {eval_set}...")
            continue
''', '''        except FileNotFoundError:
            print(f"⚠ File not found: {order_products_file}, skipping {eval_set}...")
            continue

        if not full:
            # Sample mode writes at most max(limit, 1) orders, so aggregate only those
            df_order_filtered = df_order_filtered.head(max(limit, 1))
            df_order_products = df_order_products[
                df_order_products["order_id"].isin(df_order_filtered["order_id"])
            ]
''')
assert B != PO
# repair c: attribute access instead of a Series per row
C = PO.replace('for i, (_, order) in enumerate(df_orders_vespa.iterrows()):',
               'for i, order in enumerate(df_orders_vespa.itertuples(index=False)):')
for k in ['order_id', 'user_id', 'order_dow', 'order_hour_of_day', 'days_since_prior_order', 'product_ids']:
    C = C.replace(f'order["{k}"]', f'order.{k}')
C = C.replace("f\"id:orders:order::{order['order_id']}\"", "f\"id:orders:order::{order.order_id}\"")
assert C != PO and "order[" not in C.split("doc = {")[1]

subs.append(dict(
 id="process-orders-sample-subset",
 unit="examples/workshop-ecommerce/preprocess.py::process_orders",
 changed={"examples/workshop-ecommerce/preprocess.py::process_orders": B},
 sole_caller_evidence=None,
 notes="In sample mode only the first max(limit, 1) orders are aggregated and merged, which are the only rows written; the left merge keeps order and the aggregated side is unique per order_id.",
))
subs.append(dict(
 id="process-orders-itertuples",
 unit="examples/workshop-ecommerce/preprocess.py::process_orders",
 changed={"examples/workshop-ecommerce/preprocess.py::process_orders": C},
 sole_caller_evidence=None,
 notes="Reads each order by attribute instead of building a pandas Series per row; the written documents are unchanged.",
))

ENC_SRC = open('hypencoder/encode_query.py', encoding='utf-8').read()
old = '''        body["input.query(input_ids)"] = [np.array(enc.ids, dtype=np.float32).tolist()]
        body["input.query(attention_mask)"] = [
            np.array(enc.attention_mask, dtype=np.float32).tolist()]'''
new = '''        body["input.query(input_ids)"] = [[float(i) for i in enc.ids]]
        body["input.query(attention_mask)"] = [[float(m) for m in enc.attention_mask]]'''
assert old in ENC_SRC
import ast
src = ENC_SRC.splitlines()
start = next(i for i,l in enumerate(src) if l.startswith('def main()'))
end = next(i for i,l in enumerate(src) if i > start and l.startswith('if __name__'))
fn = "\n".join(src[start:end]).rstrip()
fn_new = fn.replace(old, new)
assert fn_new != fn
subs.append(dict(
 id="encode-query-float-lists",
 unit="hypencoder/encode_query.py::main",
 changed={"hypencoder/encode_query.py::main": fn_new},
 sole_caller_evidence=None,
 notes="Builds the float lists directly instead of through two temporary numpy arrays. Token ids and mask values are below 2**24, so the values and the JSON text are identical.",
))
with open("submissions.jsonl", "a", encoding="utf-8") as f:
    for s in subs:
        f.write(json.dumps(s, ensure_ascii=False) + "\n")
print("appended", len(subs))
