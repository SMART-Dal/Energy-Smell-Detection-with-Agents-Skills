"""Cases for self_delegation_chain."""


class User:
    def get_name(self):
        # One call to another method of the same object.
        return self._read_name()

    def display(self):
        # Same shape with an argument passed through.
        return self._format(self._name)

    def summary(self):
        # Two statements: not a bare delegation.
        parts = self._read_name()
        return parts.upper()

    def label(self):
        # Reads an attribute rather than calling a method.
        return self._name

    def render(self):
        # Calls something that is not on `self`.
        return format_name(self._name)

    def described(self):
        """A docstring does not count as a statement."""
        return self._read_name()

    def combined(self):
        # Two calls in one expression is not a pass-through.
        return self._first() + self._second()


class TemperatureSensor:
    @property
    def celsius(self):
        # A decorator changes what the method is. `@property` makes this an
        # attribute read, not a frame the caller chose to pay.
        return self.get_temperature()


class BaseProcessor:
    def process(self, data):
        # The template-method pattern: the frame is the extension point, and
        # a subclass overrides the hook. Inlining it breaks the override.
        return self._do_process(data)

    def _do_process(self, data):
        raise NotImplementedError


class BatchProcessor(BaseProcessor):
    def _do_process(self, data):
        return [x for x in data]
