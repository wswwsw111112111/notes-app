
# def print_recursion(func):
#     def wrapper(*args, **kwargs):
#         print(func.__name__)
#         return func(*args, **kwargs)
#     return wrapper
#
# @print_recursion
def test(n):
    if n > 2:
        test(n - 1)
        print(n)
    else:
        print('base case')

test(5)

# print(int('12345666', base=16))


def addfuc(func):
    def cherter():
        print('%s(),你好啊'%func.__name__)
        return func()
    return cherter




def log(func):
    def wrapper(*args, **kw):
        print('call %s():' % func.__name__)
        return func(*args, **kw)
    return wrapper

@addfuc
def wode():
    print('我的===--世界')
@log
def now():
    print('2015-3-25')











