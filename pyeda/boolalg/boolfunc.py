"""
Boolean Functions

Interface Functions:
    num2point
    num2upoint
    num2term

    point2upoint
    point2term

    iter_points
    iter_upoints
    iter_terms

    vpoint2point

Interface Classes:
    Variable
    Function
"""

import functools
import operator
import re
import threading

from pyeda.util import bit_on, cached_property

VARIABLES = dict()


def var(name, index=None):
    """Return a unique Variable instance.

    .. note:: Do NOT call this function directly. It should only be used by
              concrete Variable implementations, eg ExprVariable.
    """
    tname = type(name)
    if tname is str:
        names = (name, )
    elif tname is tuple:
        names = name
    else:
        fstr = "expected name to be a str or tuple, got {0.__name__}"
        raise TypeError(fstr.format(tname))

    if not names:
        raise ValueError("expected at least one name")

    for name in names:
        tname = type(name)
        if tname is not str:
            fstr = "expected name to be a str, got {0.__name__}"
            raise TypeError(fstr.format(tname))
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", name):
            fstr = "expected name to match [a-zA-Z][a-zA-Z0-9_]*, got {}"
            raise ValueError(fstr.format(name))

    if index is None:
        indices = tuple()
    else:
        tindex = type(index)
        if tindex is int:
            indices = (index, )
        elif tindex is tuple:
            indices = index
        else:
            fstr = "expected index to be an int or tuple, got {0.__name__}"
            raise TypeError(fstr.format(tindex))

    for index in indices:
        tindex = type(index)
        if tindex is not int:
            fstr = "expected index to be an int, got {0.__name__}"
            raise TypeError(fstr.format(tindex))
        if index < 0:
            fstr = "expected index to be >= 0, got {}"
            raise ValueError(fstr.format(index))

    try:
        v = VARIABLES[(names, indices)]
    except KeyError:
        v = Variable(names, indices)
        VARIABLES[(names, indices)] = v
    return v

def num2point(num, vs):
    """Convert a number into a point in an N-dimensional space.

    Parameters
    ----------
    num : int
    vs : [Variable]
    """
    return {v: bit_on(num, i) for i, v in enumerate(vs)}

def num2upoint(num, vs):
    """Convert a number into an untyped point in an N-dimensional space.

    Parameters
    ----------
    num : int
    vs : [Variable]
    """
    upoint = [set(), set()]
    for i, v in enumerate(vs):
        upoint[bit_on(num, i)].add(v.uniqid)
    return frozenset(upoint[0]), frozenset(upoint[1])

def num2term(num, fs, conj=False):
    """Convert a number into a min/max term.

    Parameters
    ----------
    num : int
    fs : [Function]
    conj : bool
        conj=False for minterms, conj=True for maxterms

    Examples
    --------

    Table of min/max terms for Boolean space {a, b, c}

    +-----+----------+----------+
    | num |  minterm |  maxterm |
    +=====+==========+==========+
    | 0   | a' b' c' | a  b  c  |
    | 1   | a  b' c' | a' b  c  |
    | 2   | a' b  c' | a  b' c  |
    | 3   | a  b  c' | a' b' c  |
    | 4   | a' b' c  | a  b  c' |
    | 5   | a  b' c  | a' b  c' |
    | 6   | a' b  c  | a  b' c' |
    | 7   | a  b  c  | a' b' c' |
    +-------+----------+----------+
    """
    if conj:
        return tuple(~f if bit_on(num, i) else f for i, f in enumerate(fs))
    else:
        return tuple(f if bit_on(num, i) else ~f for i, f in enumerate(fs))

def point2upoint(point):
    """Convert a point into an untyped point.

    Parameters
    ----------
    point : {Variable: int}
    """
    upoint = [set(), set()]
    for v, val in point.items():
        upoint[val].add(v.uniqid)
    upoint[0] = frozenset(upoint[0])
    upoint[1] = frozenset(upoint[1])
    return tuple(upoint)

def point2term(point, conj=False):
    """Convert a point in an N-dimension space into a min/max term.

    Parameters
    ----------
    point : {Variable: int}
    """
    if conj:
        return tuple(~v if val else v for v, val in point.items())
    else:
        return tuple(v if val else ~v for v, val in point.items())

def iter_points(vs):
    """Iterate through all points in an N-dimensional space.

    Parameters
    ----------
    vs : [Variable]
    """
    for num in range(1 << len(vs)):
        yield num2point(num, vs)

def iter_upoints(vs):
    """Iterate through all untyped points in an N-dimensional space.

    Parameters
    ----------
    vs : [Variable]
    """
    for num in range(1 << len(vs)):
        yield num2upoint(num, vs)

def iter_terms(fs, conj=False):
    """Iterate through all min/max terms in an N-dimensional space.

    Parameters
    ----------
    fs : [Function]
    """
    for num in range(1 << len(fs)):
        yield num2term(num, fs, conj)

def vpoint2point(vpoint):
    """Convert a vector point to a point."""
    point = dict()
    for v, val in vpoint.items():
        point.update(_flatten(v, val))
    return point

def _flatten(v, val):
    """Recursively flatten vectorized var => {0, 1} mappings."""
    if isinstance(v, Variable):
        yield v, int(val)
    else:
        if len(v) != len(val):
            raise ValueError("expected 1:1 mapping from Variable => {0, 1}")
        for _var, _val in zip(v, val):
            yield from _flatten(_var, _val)


_UNIQIDS = dict()
_COUNT = 1

class Variable(object):
    """
    Abstract base class that defines an interface for a Boolean variable.

    A Boolean variable is a numerical quantity that may assume any value in the
    set B = {0, 1}.

    This implementation includes optional indices, nonnegative integers that
    can be used to construct multi-dimensional bit vectors.
    """
    def __init__(self, names, indices):
        global _UNIQIDS, _COUNT

        with threading.Lock():
            try:
                uniqid = _UNIQIDS[(names, indices)]
            except KeyError:
                uniqid = _COUNT
                _COUNT += 1
                _UNIQIDS[(names, indices)] = uniqid

        self.names = names
        self.indices = indices
        self.uniqid = uniqid

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        if self.indices:
            suffix = "[" + ",".join(str(idx) for idx in self.indices) + "]"
            return self.qualname + suffix
        else:
            return self.qualname

    def __lt__(self, other):
        if self.names == other.names:
            return self.indices < other.indices
        else:
            return self.names < other.names

    @property
    def name(self):
        """Return the variable name."""
        return self.names[0]

    @property
    def qualname(self):
        """Return the fully qualified name."""
        return ".".join(reversed(self.names))


class Function(object):
    """
    Abstract base class that defines an interface for a scalar Boolean function
    of :math:`N` variables.
    """

    # Operators
    def __invert__(self):
        """Boolean negation operator

        +-----------+------------+
        | :math:`f` | :math:`f'` |
        +===========+============+
        |         0 |          1 |
        +-----------+------------+
        |         1 |          0 |
        +-----------+------------+
        """
        raise NotImplementedError()

    def __or__(self, other):
        """Boolean disjunction (sum, OR) operator

        +-----------+-----------+---------------+
        | :math:`f` | :math:`g` | :math:`f + g` |
        +===========+===========+===============+
        |         0 |         0 |             0 |
        +-----------+-----------+---------------+
        |         0 |         1 |             1 |
        +-----------+-----------+---------------+
        |         1 |         0 |             1 |
        +-----------+-----------+---------------+
        |         1 |         1 |             1 |
        +-----------+-----------+---------------+
        """
        raise NotImplementedError()

    def __ror__(self, other):
        return self.__or__(other)

    def __and__(self, other):
        r"""Boolean conjunction (product, AND) operator

        +-----------+-----------+-------------------+
        | :math:`f` | :math:`g` | :math:`f \cdot g` |
        +===========+===========+===================+
        |         0 |         0 |                 0 |
        +-----------+-----------+-------------------+
        |         0 |         1 |                 0 |
        +-----------+-----------+-------------------+
        |         1 |         0 |                 0 |
        +-----------+-----------+-------------------+
        |         1 |         1 |                 1 |
        +-----------+-----------+-------------------+
        """
        raise NotImplementedError()

    def __rand__(self, other):
        return self.__and__(other)

    def __xor__(self, other):
        r"""Boolean exclusive or (XOR) operator

        +-----------+-----------+--------------------+
        | :math:`f` | :math:`g` | :math:`f \oplus g` |
        +===========+===========+====================+
        |         0 |         0 |                  0 |
        +-----------+-----------+--------------------+
        |         0 |         1 |                  1 |
        +-----------+-----------+--------------------+
        |         1 |         0 |                  1 |
        +-----------+-----------+--------------------+
        |         1 |         1 |                  0 |
        +-----------+-----------+--------------------+
        """
        raise NotImplementedError()

    def __rxor__(self, other):
        return self.__xor__(other)

    def __add__(self, other):
        from pyeda.boolalg.bfarray import farray
        if isinstance(other, Function):
            return farray([self] + [other])
        elif isinstance(other, farray):
            return farray([self] + list(other.flat))
        else:
            raise TypeError("expected Function or farray")

    def __radd__(self, other):
        from pyeda.boolalg.bfarray import farray
        if isinstance(other, Function):
            return farray([other] + [self])
        elif isinstance(other, farray):
            return farray(list(other.flat) + [self])
        else:
            raise TypeError("expected Function or farray")

    def __mul__(self, other):
        from pyeda.boolalg.bfarray import farray
        if type(other) is not int:
            raise TypeError("expected multiplier to be an int")
        if other < 0:
            raise ValueError("expected multiplier to be non-negative")
        return farray([self] * other)

    def __rmul__(self, other):
        return self.__mul__(other)

    @property
    def support(self):
        r"""Return the support set of a function.

        Let :math:`f(x_1, x_2, \dots, x_n)` be a Boolean function of :math:`N`
        variables.

        The unordered set :math:`\{x_1, x_2, \dots, x_n\}` is called the
        *support* of the function.
        """
        raise NotImplementedError()

    @cached_property
    def usupport(self):
        """Return the untyped support set of a function."""
        return frozenset(v.uniqid for v in self.support)

    @property
    def inputs(self):
        """Return the support set in name/index order."""
        raise NotImplementedError()

    @property
    def top(self):
        """Return the first variable in the ordered support set."""
        if self.inputs:
            return self.inputs[0]
        else:
            return None

    @property
    def degree(self):
        r"""Return the degree of a function.

        A function from :math:`B^{N} \Rightarrow B` is called a Boolean
        function of *degree* :math:`N`.
        """
        return len(self.support)

    @property
    def cardinality(self):
        r"""Return the cardinality of the relation :math:`B^{N} \Rightarrow B`.

        Always equal to :math:`2^{N}`.
        """
        return 1 << self.degree

    def iter_domain(self):
        """Iterate through all points in the domain."""
        yield from iter_points(self.inputs)

    def iter_image(self):
        """Iterate through all elements in the image."""
        for point in iter_points(self.inputs):
            yield self.restrict(point)

    def iter_relation(self):
        """Iterate through all (point, element) pairs in the relation."""
        for point in iter_points(self.inputs):
            yield (point, self.restrict(point))

    def restrict(self, point):
        r"""
        Return the Boolean function that results after restricting a subset of
        its input variables to :math:`\{0, 1\}`.

        :math:`f \: | \: x_i = b`
        """
        return self.urestrict(point2upoint(point))

    def urestrict(self, upoint):
        """Implementation of restrict that requires an untyped point."""
        raise NotImplementedError()

    def vrestrict(self, vpoint):
        """Expand all vectors before applying 'restrict'."""
        return self.restrict(vpoint2point(vpoint))

    def compose(self, mapping):
        r"""
        Return the Boolean function that results after substituting a subset of
        its input variables for other Boolean functions.

        :math:`f_1 \: | \: x_i = f_2`
        """
        raise NotImplementedError()

    def satisfy_one(self):
        """
        If this function is satisfiable, return a satisfying input point. A
        tautology *may* return a zero-dimensional point; a contradiction *must*
        return None.
        """
        raise NotImplementedError()

    def satisfy_all(self):
        """Iterate through all satisfying input points."""
        raise NotImplementedError()

    def satisfy_count(self):
        """Return the cardinality of the set of all satisfying input points."""
        return sum(1 for _ in self.satisfy_all())

    def iter_cofactors(self, vs=None):
        r"""Iterate through the cofactors of a function over N variables.

        The *cofactor* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)`
        with respect to variable :math:`x_i` is:
        :math:`f_{x_i} = f(x_1, x_2, \dots, 1, \dots, x_n)`

        The *cofactor* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)`
        with respect to variable :math:`x_i'` is:
        :math:`f_{x_i'} = f(x_1, x_2, \dots, 0, \dots, x_n)`
        """
        vs = self._expect_vars(vs)
        for upoint in iter_upoints(vs):
            yield self.urestrict(upoint)

    def cofactors(self, vs=None):
        r"""Return a tuple of the cofactors of a function over N variables.

        The *cofactor* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)`
        with respect to variable :math:`x_i` is:
        :math:`f_{x_i} = f(x_1, x_2, \dots, 1, \dots, x_n)`

        The *cofactor* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)`
        with respect to variable :math:`x_i'` is:
        :math:`f_{x_i'} = f(x_1, x_2, \dots, 0, \dots, x_n)`
        """
        return tuple(cf for cf in self.iter_cofactors(vs))

    def smoothing(self, vs=None):
        r"""Return the smoothing of a function over a sequence of N variables.

        The *smoothing* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)` with
        respect to variable :math:`x_i` is:
        :math:`S_{x_i}(f) = f_{x_i} + f_{x_i'}`

        This is the same as the existential quantification operator:
        :math:`\exists \{x_1, x_2, \dots\} \: f`
        """
        return functools.reduce(operator.or_, self.iter_cofactors(vs))

    def consensus(self, vs=None):
        r"""Return the consensus of a function over a sequence of N variables.

        The *consensus* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)` with
        respect to variable :math:`x_i` is:
        :math:`C_{x_i}(f) = f_{x_i} \cdot f_{x_i'}`

        This is the same as the universal quantification operator:
        :math:`\forall \{x_1, x_2, \dots\} \: f`
        """
        return functools.reduce(operator.and_, self.iter_cofactors(vs))

    def derivative(self, vs=None):
        r"""Return the derivative of a function over a sequence of N variables.

        The *derivative* of :math:`f(x_1, x_2, \dots, x_i, \dots, x_n)` with
        respect to variable :math:`x_i` is:
        :math:`\frac{\partial}{\partial x_i} f = f_{x_i} \oplus f_{x_i'}`

        This is also known as the Boolean *difference*.
        """
        return functools.reduce(operator.xor, self.iter_cofactors(vs))

    def is_zero(self):
        """Return whether this function is zero.

        .. note:: This method will only look for a particular "zero form",
                  and will **NOT** do a full search for a contradiction.
        """
        raise NotImplementedError()

    def is_one(self):
        """Return whether this function is one.

        .. note:: This method will only look for a particular "one form",
                  and will **NOT** do a full search for a tautology.
        """
        raise NotImplementedError()

    @staticmethod
    def box(obj):
        """Convert primitive types to a Function."""
        raise NotImplementedError()

    def unbox(self):
        """Return integer 0 or 1 if possible, otherwise return the Function."""
        if self.is_zero():
            return 0
        elif self.is_one():
            return 1
        else:
            return self

    @staticmethod
    def _expect_vars(vs=None):
        """Verify the input type and return a list of Variables."""
        if vs is None:
            return list()
        elif isinstance(vs, Variable):
            return [vs]
        else:
            checked = list()
            # Will raise TypeError if vs is not iterable
            for v in vs:
                if isinstance(v, Variable):
                    checked.append(v)
                else:
                    fstr = "expected Variable, got {0.__name__}"
                    raise TypeError(fstr.format(type(v)))
            return checked

