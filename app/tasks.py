import time

def example(seconds):
    print('Start')
    for i in range(seconds):
        print(i)
        time.sleep(1)
    print('End')
