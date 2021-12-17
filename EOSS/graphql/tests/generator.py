import random
import asyncio
import time
import timeit
from concurrent.futures import ProcessPoolExecutor


class A:
    @staticmethod
    def add(a=1, b=2):
        print('--> ADD',a+b)

    @staticmethod
    def add_wrapper():
        print('--> WRAP')
        A.add()

class B(A):

    def run(self):
        self.add_wrapper()


def main3():
    # test_func('test')
    test = B()
    test.run()







def cpu_sweatjob(some_param):
    start = timeit.default_timer()
    print('--> HELLA CALCS:', some_param)
    return start



async def some_func():
    print('--> RUNNING FUNC')
    loop = asyncio.get_running_loop()

    start = timeit.default_timer()
    with ProcessPoolExecutor(max_workers=1) as pool:
        func_time = await loop.run_in_executor(pool, cpu_sweatjob, '888')
        stop = timeit.default_timer()

        total = stop - start
        boot = func_time - start
        func_run = stop - func_time

        print('--> FINAL TIME:', boot / total, func_run / total)



def main2():
    print('--> RUNNING MAIN')
    asyncio.run(some_func())












def generator(start=1, end=1000):
    while True:
        print('--> CALL')
        stop = (yield random.randint(start, end))
        print('stop', stop)
        if stop is True:
            yield "generator function stopped"



def main():
    print('--> STARTED')

    test = ['1', '2', '4']

    print(','.join(test))

    gen = generator()
    print('--> GENERATOR OBJECT:', gen, '\n\n\n')

    print(' ------------------- ')
    print('--> SENDING None:', next(gen))
    print(' ------------------- ', '\n\n')

    print(' ------------------- ')
    print('--> SENDING None:', next(gen))
    print(' ------------------- ', '\n\n')

    print(' ------------------- ')
    print('--> SENDING smth:', gen.send('smth'))
    print(' ------------------- ', '\n\n')




if __name__ == "__main__":
    main3()