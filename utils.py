def login_required(func):
    '''Decorator to check if users are logged in'''
    def wrapper(*args, **kwargs):
        print(dir(args[1]))
        print(args[1].context)
        user = args[1].context.get('user')
        if user is None:
            raise Exception('Not Authenticated')
        return func(*args, **kwargs)
    return wrapper