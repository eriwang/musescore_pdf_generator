from musescore.score import Score


def main():
    s = Score.create_from_file('C:/Users/johne/Desktop/Gurenge.mscz')
    print(s)


if __name__ == '__main__':
    main()
