def parse_page(html):
    script = {
        "before": [],
        "steps": [],
        "after": []
    }

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all(lambda tag: (tag.name == "pre" or tag.name == "div" or tag.name == "p") and tag.has_attr("data-test")):
        attr = tag.attrs["data-test"]

        if attr == "before":
            script["before"].extend(parse_cmds(tag.string, tag.attrs))

        if attr == "exec":
            script["steps"].extend(parse_cmds(tag.string, tag.attrs))

        if attr == "file":
            script["steps"].append(parse_file(tag.contents, tag.attrs))

        if attr == "after":
            script["after"].extend(parse_cmds(tag.string, tag.attrs))

        if re.search("^run-macro", attr):
            macro = re.sub("run-macro\s?", "", attr)
            script["steps"].extend(get_macro(macro))

    return script
