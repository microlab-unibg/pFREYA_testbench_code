def bitstring_to_bytes(s):
    """Converts a string to a bytearray if str is 8 bits

    Parameters
    ----------
    s : str
        String to be converted

    Returns
    -------
    byteBytes to be sent
    """
    bitstr = s.replace('_','') # trim the hex divider
    return int(bitstr, 2).to_bytes((len(bitstr) + 7) // 8, byteorder='big')