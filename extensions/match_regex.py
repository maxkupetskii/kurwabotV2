import re


class RegexEqual(str):
    """Override str.__eq__ to match a regex pattern.

    The RegexEqual class inherits from str and overrides the
    __eq__() method to match a regular expression:

        >>> RegexEqual('hello') == 'h.*o'
        True

    This is used in the match-clause (not a case clause).
    It will match cases with a regex for a literal pattern:

        >>> match RegexEqual('the tale of two cities'):
        ...     case 's...y':
        ...         print('A sad story')
        ...     case 't..e':
        ...         print('A mixed tale')
        ...     case 's..a':
        ...         print('A long read')
        ...
        A mixed tale
    """

    def __eq__(self, pattern):
        return bool(re.search(pattern, self))
