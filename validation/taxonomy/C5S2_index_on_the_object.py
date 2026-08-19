"""C5.S2 Missing Helper Type -- the index belongs to the object, not the call.

The card's third repair example: an index has to be built where the data
arrives and read where the question is asked, so two methods change and it is
still one repair. It also creates an obligation the card names -- `products`
must not be mutated afterwards without the index being updated -- which is why
both classes keep the original list.
"""

class BeforeCatalog:
    __slots__ = ("products",)

    def __init__(self, products):
        self.products = products

    def price_of(self, sku):
        for product in self.products:
            if product[0] == sku:
                return product[1]
        raise KeyError(sku)


class AfterCatalog:
    __slots__ = ("products", "_by_sku")

    def __init__(self, products):
        self.products = products
        self._by_sku = {p[0]: p[1] for p in products}

    def price_of(self, sku):
        try:
            return self._by_sku[sku]
        except KeyError:
            raise KeyError(sku) from None


def before(products, skus):
    catalog = BeforeCatalog(products)
    return sum(catalog.price_of(s) for s in skus)


def after(products, skus):
    catalog = AfterCatalog(products)
    return sum(catalog.price_of(s) for s in skus)


def _catalog(n):
    return [(f"sku{i}", i) for i in range(n)]


def cases():
    return [("many-lookups", lambda: (_catalog(4_000), [f"sku{i % 4000}" for i in range(8_000)])),
            ("one-lookup",   lambda: (_catalog(4_000), ["sku1"])),
            ("edge",         lambda: (_catalog(1), ["sku0"]))]
