SPECS = [
    {
        "id": "dxlog-truncate-bisect",
        "unit": "src/python/dxpy/dxlog.py::DXLogHandler.truncate_message",
        "funcs": [
            {
                "unit": "src/python/dxpy/dxlog.py::DXLogHandler.truncate_message",
                "replacements": [[
                    "        msg_bytes = msg_bytes[:8000]\n"
                    "        while len(json.dumps(_bytes2utf8(msg_bytes))) > 8000:\n"
                    "            msg_bytes = msg_bytes[:-1]\n"
                    "\n"
                    "        message = _bytes2utf8(msg_bytes)\n",
                    "        msg_bytes = msg_bytes[:8000]\n"
                    "        low, high = 0, len(msg_bytes)\n"
                    "        while low < high:\n"
                    "            mid = (low + high + 1) // 2\n"
                    "            if len(json.dumps(_bytes2utf8(msg_bytes[:mid]))) <= 8000:\n"
                    "                low = mid\n"
                    "            else:\n"
                    "                high = mid - 1\n"
                    "\n"
                    "        message = _bytes2utf8(msg_bytes[:low])\n",
                ]],
            },
        ],
        "sole_caller_evidence": "grep over src, build and doc: truncate_message is referenced only at src/python/dxpy/dxlog.py:94, inside emit. The repair keeps the return value and the exception for None input, since message.encode runs first in both.",
        "notes": "Bisection on the prefix length. The predicate is monotone because bytes.decode with ignore is prefix-stable and json.dumps length never shrinks as characters are added, so the result equals the decrement loop's result.",
    },
    {
        "id": "coding-display-position-dict",
        "unit": "src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe",
        "funcs": [
            {
                "unit": "src/python/dxpy/cli/dataset_utilities.py::DXDatasetDictionary.create_coding_name_dframe",
                "replacements": [
                    [
                        '            display = coding.get("display") or []\n',
                        '            display = coding.get("display") or []\n'
                        '            first_position = {}\n'
                        '            for position, code in enumerate(display):\n'
                        '                first_position.setdefault(code, position)\n',
                    ],
                    [
                        "                        int(display.index(c) + 1) if c in display else None\n",
                        "                        int(first_position[c] + 1) if c in first_position else None\n",
                    ],
                ],
            },
        ],
        "sole_caller_evidence": "create_coding_name_dframe is called only at src/python/dxpy/cli/dataset_utilities.py:2225. The repair changes only the flat-coding branch's display_order list; the returned frame has the same columns, values and dtypes for hashable codes.",
        "notes": "A first-position dict built once, so each code is a dict lookup instead of two linear scans of display. setdefault keeps the first occurrence, as list.index does.",
    },
    {
        "id": "validate-ids-comprehension",
        "unit": "src/python/dxpy/cli/dataset_utilities.py::validate_cohort_ids",
        "funcs": [
            {
                "unit": "src/python/dxpy/cli/dataset_utilities.py::validate_cohort_ids",
                "replacements": [[
                    "    id_list = reduce(lambda_for_list_conv, ids, [])\n",
                    "    id_list = [lambda_for_list_conv([], b)[0] for b in ids]\n",
                ]],
            },
        ],
        "sole_caller_evidence": "validate_cohort_ids is called only at src/python/dxpy/cli/dataset_utilities.py:1877, which uses both returned values. The returned lambda_for_list_conv is unchanged and still used by its other caller. The list built is the same as reduce would build, element by element, with the same conversion errors.",
        "notes": "Each id is converted by the same lambda, applied to an empty list, so the cost is linear in ids and the lambda is not copied in a loop.",
    },
    {
        "id": "output-colset-once",
        "unit": "src/python/dxpy/cli/output_handling.py::write_expression_output",
        "funcs": [
            {
                "unit": "src/python/dxpy/cli/output_handling.py::write_expression_output",
                "replacements": [[
                    "        if not all(\n"
                    "            set(i.keys()) == set(COLUMN_NAMES) for i in output_listdict_or_string\n"
                    "        ):",
                    "        column_name_set = set(COLUMN_NAMES)\n"
                    "        if not all(\n"
                    "            set(i.keys()) == column_name_set for i in output_listdict_or_string\n"
                    "        ):",
                ]],
            },
        ],
        "sole_caller_evidence": "write_expression_output is called at src/python/dxpy/cli/dataset_utilities.py:1701 and in src/python/test/test_extract_expression.py. COLUMN_NAMES is a local, so no other reader of the changed name exists. The column-set check gives the same result for every row.",
        "notes": "COLUMN_NAMES is fixed before the check, so its set is built once instead of once per row.",
    },
    {
        "id": "find-stop-at-limit",
        "unit": "src/python/dxpy/bindings/search.py::_find",
        "funcs": [
            {
                "unit": "src/python/dxpy/bindings/search.py::_find",
                "replacements": [[
                    '        if resp["next"] is not None:\n'
                    '            query["starting"] = resp["next"]\n'
                    '            query["limit"] = min(query["limit"]*2, 1000)\n'
                    "        else:\n",
                    '        if resp["next"] is not None:\n'
                    '            query["starting"] = resp["next"]\n'
                    '            query["limit"] = min(query["limit"]*2, 1000)\n'
                    "            if num_results == limit:\n"
                    "                return\n"
                    "        else:\n",
                ]],
            },
        ],
        "sole_caller_evidence": "_find is called from the find_* wrappers in src/python/dxpy/bindings/search.py (lines 270, 426, 540, 636, 1023) and at 805, 885, 1005 through _org_find. Each caller receives the same generator items. The repair still sets query starting and limit before returning, so the caller's query dict ends in the same state.",
        "notes": "When the consumer's limit lands on the last item of a page that has a next token, the original fetches one more page before its limit check returns. The repair returns before that request, after updating the query exactly as the original would.",
    },
    {
        "id": "pool-manager-cache",
        "unit": "src/python/dxpy/__init__.py::_get_pool_manager",
        "funcs": [
            {
                "unit": "src/python/dxpy/__init__.py::_get_pool_manager",
                "replacements": [
                    [
                        "        # manager.\n"
                        "        pool_args = dict(default_pool_args,\n",
                        "        # manager.\n"
                        "        pool_key = (verify, cert_file, key_file, ssl_context, os.environ.get('DX_CA_CERT'),\n"
                        "                    'DX_USE_OS_CA_BUNDLE' in os.environ, _get_env_var_proxy())\n"
                        "        try:\n"
                        "            hash(pool_key)\n"
                        "        except TypeError:\n"
                        "            pool_key = None\n"
                        "        pool_cache = _get_pool_manager.__dict__.setdefault('pool_cache', {})\n"
                        "        if pool_key is not None and pool_key in pool_cache:\n"
                        "            if _get_env_var_proxy():\n"
                        "                _get_env_var_proxy(print_proxy=True)\n"
                        "            return pool_cache[pool_key]\n"
                        "        pool_args = dict(default_pool_args,\n",
                    ],
                    [
                        "            pool_args.update(proxy_params)\n"
                        "            return urllib3.ProxyManager(**pool_args)\n"
                        "        else:\n"
                        "            return urllib3.PoolManager(**pool_args)\n",
                        "            pool_args.update(proxy_params)\n"
                        "            pool_manager = urllib3.ProxyManager(**pool_args)\n"
                        "        else:\n"
                        "            pool_manager = urllib3.PoolManager(**pool_args)\n"
                        "        if pool_key is not None:\n"
                        "            pool_cache[pool_key] = pool_manager\n"
                        "        return pool_manager\n",
                    ],
                ],
            },
        ],
        "sole_caller_evidence": "_get_pool_manager is called only at src/python/dxpy/__init__.py lines 591 (DXHTTPRequest) and 727 (its except path, which calls clear on the result). No other reference in src, build or doc. The cache is stored as an attribute of the function, so no module-level name is added, and the proxy message is printed on each call as before.",
        "notes": "The uncommon branch builds a new urllib3 pool on every call. The repair returns the pool built for the same verify, cert, key, ssl_context, DX_CA_CERT, DX_USE_OS_CA_BUNDLE and proxy inputs.",
    },
    {
        "id": "depends-on-no-discarded-describe",
        "unit": "src/python/dxpy/utils/local_exec_utils.py::wait_for_depends_on",
        "funcs": [
            {
                "unit": "src/python/dxpy/utils/local_exec_utils.py::wait_for_depends_on",
                "replacements": [[
                    "                    handler = dxpy.get_handler(an_id)\n"
                    "                    desc = handler.describe()\n",
                    "                    handler = dxpy.get_handler(an_id)\n",
                ]],
            },
        ],
        "sole_caller_evidence": "wait_for_depends_on is called only at src/python/dxpy/utils/local_exec_utils.py:317. The removed describe result was bound to desc and never read, and handler._wait_on_close still makes its own state request, so the wait, the exception wrapper and the printed lines are unchanged.",
        "notes": "One describe request per non-job, non-local data object in depends_on is removed.",
    },
]
