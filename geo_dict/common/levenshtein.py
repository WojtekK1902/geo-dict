# coding=utf-8

def lev_dist(s1, s2):
    l1, l2 = len(s1), len(s2)
    diacr = {u'ą':'a', u'ć':'c', u'ę':'e', u'ł':'l', u'ń':'n', u'ó':'o', u'ś':'s', u'ż':'z', u'ź':'z'}

    curr = [x for x in range(l1+1)]
    prev = []

    for i in range(l2):
        prev2, prev, curr = prev, curr, [i+1]+[0]*l1
        for j in range(l1):
            cost = 0
            if s1[j] != s2[i]:
                cost = 1
            curr[j+1] = min(curr[j]+1, prev[j+1]+1, prev[j]+cost)

            #spelling mistakes
            if s1[j] == u'ó' and s2[i] == 'u':
                curr[j+1] = min(curr[j+1], prev[j]+0.5)
            if s1[j] == 'u' and s2[i] == u'ó':
                curr[j+1] = min(curr[j+1], prev[j]+0.5)
            if s1[j] == u'ż' and s2[i] == 'z' and i > 0 and s2[i-1] == 'r':
                curr[j+1] = min(curr[j+1], prev2[j]+0.5)
            if s1[j] == 'z' and j > 0 and s1[j-1] == 'r' and s2[i] == u'ż':
                curr[j+1] = min(curr[j+1], prev[j-1]+0.5)
            if s1[j] == 'h' and s2[i] == 'h' and i > 0 and s2[i-1] == 'c':
                curr[j+1] = min(curr[j+1], prev2[j]+0.5)
            if s1[j] == 'h' and j > 0 and s1[j-1] == 'c' and s2[i] == 'h':
                curr[j+1] = min(curr[j+1], prev[j-1]+0.5)
            if s1[j] == u'ą' and s2[i] == 'm' and i > 0 and s2[i-1] == 'o':
                curr[j+1] = min(curr[j+1], prev2[j]+0.5)
            if s1[j] == 'm' and j > 0 and s1[j-1] == 'o' and s2[i] == u'ą':
                curr[j+1] = min(curr[j+1], prev[j-1]+0.5)
            if s1[j] == u'ę' and s2[i] == 'm' and i > 0 and s2[i-1] == 'e':
                curr[j+1] = min(curr[j+1], prev2[j]+0.5)
            if s1[j] == 'm' and j > 0 and s1[j-1] == 'e' and s2[i] == u'ę':
                curr[j+1] = min(curr[j+1], prev[j-1]+0.5)

            #diacritic marks:
            if diacr.get(s1[j]) == s2[i] or diacr.get(s2[i]) == s1[j]:
                curr[j+1] = min(curr[j+1], prev[j]+0.25)

            #typo ('czeski błąd'):
            if i > 0 and j > 0 and s1[j] == s2[i-1] and s1[j-1] == s2[i]:
                curr[j+1] = min(curr[j+1], prev2[j-1]+0.25)

    return curr[l1]