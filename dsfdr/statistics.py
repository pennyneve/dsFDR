import numpy as np
from scipy.stats import rankdata
from scipy.stats import find_repeats
from math import sqrt


# different methods to calculate test statistic
def meandiff(data, labels):
    mean0 = np.mean(data[:, labels == 0], axis=1)
    mean1 = np.mean(data[:, labels == 1], axis=1)
    tstat = mean1 - mean0
    return tstat


def stdmeandiff(data, labels):
    mean0 = np.mean(data[:, labels == 0], axis=1)
    mean1 = np.mean(data[:, labels == 1], axis=1)
    sd0 = np.std(data[:, labels == 0], axis=1, ddof=1)
    sd1 = np.std(data[:, labels == 1], axis=1, ddof=1)
    tstat = (mean1 - mean0) / (sd1 + sd0)
    return tstat


# calculate test statistic for Mann Whitney
def mannwhitneyU(x, y):
    n1 = len(x)
    n2 = len(y)
    ranked = rankdata(np.concatenate((x, y)))
    # default: average for ties
    rankx = ranked[0:n1]
    Ux = n1 * n2 + (n1 * (n1 + 1)) / 2.0 - np.sum(rankx, axis=0)
    Uy = n1 * n2 - Ux
    U = min(Ux, Uy)
    return U


def mannwhitney(data, labels):
    group0 = data[:, labels == 0]
    group1 = data[:, labels == 1]
    tstat = np.array([mannwhitneyU(group0[i, :], group1[i, :])
                     for i in range(np.shape(data)[0])])
    return tstat

def pairedwilcoxU(x, y):
    #x, y = map(asarray, (x, y))
    d = x - y
    d = np.compress(np.not_equal(d, 0), d, axis=-1)
    r = rankdata(abs(d))
    r_plus = np.sum((d > 0) * r, axis=0)
    r_minus = np.sum((d < 0) * r, axis=0)
    
    T = min(r_plus, r_minus)
    return T
    
    #count = len(d)
    #mn = count * (count + 1.) * 0.25
    #se = count * (count + 1.) * (2. * count + 1.)
    #
    #correction = False
    #
    #replist, repnum = find_repeats(r)
    #if repnum.size != 0:
    #    # Correction for repeated elements.
    #    se -= 0.5 * (repnum * (repnum * repnum - 1)).sum()
    #
    #se = sqrt(se / 24)
    #correction = 0.5 * int(bool(correction)) * np.sign(T - mn)
    #z = (T - mn - correction) / se
    #
    #return z

def pairedwilcox(data, labels):
    group0 = data[:, labels == 0]
    group1 = data[:, labels == 1]
    tstat = np.array([pairedwilcoxU(group0[i, :], group1[i, :]) 
                      for i in range(np.shape(data)[0])])
    return tstat

# calculate test statistic for Kruskal-Wallis
def tiecorrect(rankvals):
    arr = np.sort(rankvals)
    idx = np.nonzero(np.r_[True, arr[1:] != arr[:-1], True])[0]
    cnt = np.diff(idx).astype(np.float64)

    size = np.float64(arr.size)
    return 1.0 if size < 2 else 1.0 - (cnt**3 - cnt).sum() / (size**3 - size)


def _chk_asarray(a, axis):
    if axis is None:
        a = np.ravel(a)
        outaxis = 0
    else:
        a = np.asarray(a)
        outaxis = axis

    if a.ndim == 0:
        a = np.atleast_1d(a)

    return a, outaxis


def _square_of_sums(a, axis=0):
    a, axis = _chk_asarray(a, axis)
    s = np.sum(a, axis)
    if not np.isscalar(s):
        return s.astype(float) * s
    else:
        return float(s) * s


def kruskalH(args):
    num_groups = len(args)
    if num_groups < 2:
        raise ValueError("Need at least two groups in stats.kruskal()")
    n = np.asarray(list(map(len, args)))  # samples in each group
    alldata = np.concatenate(args)
    ranked = rankdata(alldata)
    ties = tiecorrect(ranked)
    if ties == 0:
        raise ValueError('All numbers are identical in kruskal')
    # Compute sum^2/n for each group and sum
    j = np.insert(np.cumsum(n), 0, 0)
    ssbn = 0
    for i in range(num_groups):
        ssbn += _square_of_sums(ranked[j[i]:j[i + 1]]) / float(n[i])

    totaln = np.sum(n)
    h = 12.0 / (totaln * (totaln + 1)) * ssbn - 3 * (totaln + 1)
    h /= ties
    return h


def kruwallis(data, labels):
    n = len(np.unique(labels))
    allt = []
    for cbact in range(np.shape(data)[0]):
        group = []
        for j in range(n):
            group.append(data[cbact, labels == j])
        tstat = kruskalH(group)
        allt.append(tstat)
    return allt


# chi-square test (for Justine)


# pearson correlation
def _sum_of_squares(a, axis=0):
    a, axis = _chk_asarray(a, axis)
    return np.sum(a * a, axis)


def pearsonR(x, y):
    mx = x.mean()
    my = y.mean()
    xm, ym = x - mx, y - my
    r_num = np.add.reduce(xm * ym)
    r_den = np.sqrt(_sum_of_squares(xm) * _sum_of_squares(ym))
    r = r_num / r_den
    return r


# spearman correlation
def spearmanR(a, b=None, axis=0):
    a, axisout = _chk_asarray(a, axis)
    ar = np.apply_along_axis(rankdata, axisout, a)

    br = None
    if b is not None:
        b, axisout = _chk_asarray(b, axis)
        br = np.apply_along_axis(rankdata, axisout, b)
    rs = np.corrcoef(ar, br, rowvar=axisout)
    if rs.shape == (2, 2):
        return rs[1, 0]
    else:
        return rs


def spearman(data, labels):
    tstat = np.array([spearmanR(data[i, :], labels)
                      for i in range(np.shape(data)[0])])
    return tstat
