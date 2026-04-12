# Architecture — Job Cancellation

Adds a cancellable job state machine:

pending → running → completed
            ↓
        cancelling → cancelled
