def print_board(board):
    print("\nCurrent Board:")
    for row in board:
        print(" | ".join(row))
    print()

def check_winner(board, player):
    # Rows
    for row in range(3):
        if all(cell == player for cell in board[row]):
            return True
    # Columns
    for col in range(3):
        if all(board[row][col] == player for row in range(3)):
            return True
    # Diagonals
    if board[0][0] == board[1][1] == board[2][2] == player:
        return True
    if board[0][2] == board[1][1] == board[2][0] == player:
        return True
    return False

def check_draw(board):
    return all(board[row][col] != "" for row in range(3) for col in range(3))

def main():
    board = [["" for _ in range(3)] for _ in range(3)]
    current_player = "X"

    while True:
        print_board(board)
        print(f"Player {current_player}, it's your turn.")
        
        # Get user input
        valid_move = False
        while not valid_move:
            try:
                row = int(input("Enter row (0-2): "))
                col = int(input("Enter col (0-2): "))
                if 0 <= row < 3 and 0 <= col < 3 and board[row][col] == "":
                    board[row][col] = current_player
                    valid_move = True
                else:
                    print("Invalid move. Try again.")
            except ValueError:
                print("Please enter numeric values only.")

        # Check win/draw
        if check_winner(board, current_player):
            print_board(board)
            print(f"Player {current_player} wins!")
            break
        elif check_draw(board):
            print_board(board)
            print("It's a draw!")
            break

        # Switch player
        current_player = "O" if current_player == "X" else "X"

if __name__ == "__main__":
    main()
