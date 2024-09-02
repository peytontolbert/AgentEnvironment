import random

# Generate a random number between 1 and 100
secret_number = random.randint(1, 100)

print("I'm thinking of a number between 1 and 100. Can you guess it?")

while True:
    # Prompt the user to enter their guess
    guess = int(input("Enter your guess: "))
    
    # Compare the user's guess to the secret number
    if guess < secret_number:
        print("Too low!")
    elif guess > secret_number:
        print("Too high!")
    else:
        print("Correct!")
        break  # Exit the loop since they guessed correctly
