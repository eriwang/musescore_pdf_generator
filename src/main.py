from musescore.score import Score


def main():
    # get scores (somehow)
    # split
    # toss into musescore pdf conversion
    # look at pdfs make sure they're legit
    s = Score.create_from_file('C:/Users/johne/Desktop/Gurenge.mscz')
    print(s)


if __name__ == '__main__':
    main()
