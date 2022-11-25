def find_key_signature(previous_notes, key_signature_table):
    # 0 is C major,  1 is Db major,  2 is D major,  3 is D# major, 4 is E major,   5 is F major,  6 is F# major,  7 is G major,  8 is G# major, 9 is A major,   10 is A# major, 11 is B major
    # 12 is A minor, 13 is A# minor, 14 is B minor, 15 is C minor, 16 is C# minor, 17 is D minor, 18 is D# minor, 19 is E minor, 20 is F minor, 21 is F# minor, 22 is G minor,  23 is G# minor
    key_signature_weights = [0] * 24

    for i in previous_notes:
        for j in range(0, 24):
            key_signature_weights[j] += key_signature_table[j][i % 12]

    return key_signature_weights.index(max(key_signature_weights))  # not optimized


def get_key_signature_table():
    key_signature_table = [[-40] * 12 for _ in range(24)]
    for i in range(0, 12):  # loop through major keys
        key_signature_table[i][i] = 1.5
        key_signature_table[i][(i + 2) % 12] = 1
        key_signature_table[i][(i + 4) % 12] = 1
        key_signature_table[i][(i + 5) % 12] = 0.5
        key_signature_table[i][(i + 7) % 12] = 1
        key_signature_table[i][(i + 9) % 12] = 1
        key_signature_table[i][(i + 11) % 12] = 0.5
    for i in range(12, 24):  # loop through minor keys
        key_signature_table[i][i % 12] = 1.5
        key_signature_table[i][(i + 2) % 12] = 0.5
        key_signature_table[i][(i + 3) % 12] = 1
        key_signature_table[i][(i + 5) % 12] = 1
        key_signature_table[i][(i + 7) % 12] = 1
        key_signature_table[i][(i + 8) % 12] = 0.5
        key_signature_table[i][(i + 10) % 12] = 1
    return key_signature_table
