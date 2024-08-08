# Get the ordinal for an int
def get_ordinal(num : int):
    if num > 9:
        secondToLastDigit = str(num)[-2]
        if secondToLastDigit == '1':
            return str(num)+'th'
    lastDigit = num % 10
    if (lastDigit == 1):
        return str(num)+'st'
    elif (lastDigit == 2):
        return str(num)+'nd'
    elif (lastDigit == 3):
        return str(num)+'rd'
    else:
        return str(num)+'th'