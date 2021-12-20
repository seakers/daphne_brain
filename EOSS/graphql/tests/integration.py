
def test(*args):
    print('--> TEST:', *args)
    print(type(args))


def main():
    print('--> TESTING')
    test('smth', 'yessir')








if __name__ == "__main__":
    main()