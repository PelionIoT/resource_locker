class Aspects:
    lock_request_count = 'lock_request_count'
    lock_acquire_count = 'lock_acquire_count'
    lock_release_count = 'lock_release_count'
    lock_release_wait = 'lock_release_wait'
    lock_acquire_wait = 'lock_acquire_wait'
    lock_acquire_fail_count = 'lock_acquire_fail_count'

    @staticmethod
    def validate(*aspects):
        for aspect in aspects:
            if not hasattr(Aspects, aspect):
                raise ValueError(f'aspect {repr(aspect)} not supported')
