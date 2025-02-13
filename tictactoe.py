import tkinter as tk
from tkinter import messagebox

class TicTacToe:
    def __init__(self, root):
        self.root = root
        self.root.title("Tic-Tac-Toe")
        
        # Keep track of the board state: 3x3 array of "" (empty), "X", or "O"
        self.board = [["" for _ in range(3)] for _ in range(3)]
        
        # Current player: "X" or "O"
        self.current_player = "X"
        
        # Create a label to display which player's turn it is
        self.status_label = tk.Label(root, text=f"{self.current_player}'s Turn",
                                     font=("Arial", 14))
        self.status_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        # Create the 3x3 grid of buttons
        self.buttons = []
        for r in range(3):
            row_buttons = []
            for c in range(3):
                btn = tk.Button(root, text="", width=6, height=3,
                                font=("Arial", 18, "bold"),
                                command=lambda row=r, col=c: self.handle_click(row, col))
                btn.grid(row=r+1, column=c, padx=5, pady=5)
                row_buttons.append(btn)
            self.buttons.append(row_buttons)
        
        # Create a reset button below the grid
        self.reset_button = tk.Button(root, text="Reset Game", font=("Arial", 12),
                                      command=self.reset_game)
        self.reset_button.grid(row=4, column=0, columnspan=3, pady=10)
    
    def handle_click(self, row, col):
        """Handle a player's move by clicking on a cell."""
        if self.board[row][col] == "" and not self.check_winner():
            # Place the current player's mark on the board
            self.board[row][col] = self.current_player
            self.buttons[row][col].config(text=self.current_player)
            
            # Check for a winner or tie
            winner = self.check_winner()
            if winner:
                self.end_game(winner)
            else:
                # Switch to the other player
                self.current_player = "O" if self.current_player == "X" else "X"
                self.status_label.config(text=f"{self.current_player}'s Turn")
    
    def check_winner(self):
        """
        Check the board for a winner or a tie.
        Returns:
          "X" or "O" if there's a winner,
          "Tie" if the board is full and no winner,
          None otherwise.
        """
        # Check rows
        for row in range(3):
            if (self.board[row][0] == self.board[row][1] == self.board[row][2] != ""):
                return self.board[row][0]

        # Check columns
        for col in range(3):
            if (self.board[0][col] == self.board[1][col] == self.board[2][col] != ""):
                return self.board[0][col]
        
        # Check diagonals
        if (self.board[0][0] == self.board[1][1] == self.board[2][2] != ""):
            return self.board[0][0]
        if (self.board[0][2] == self.board[1][1] == self.board[2][0] != ""):
            return self.board[0][2]
        
        # Check for tie (no empty squares)
        if all(self.board[r][c] != "" for r in range(3) for c in range(3)):
            return "Tie"
        
        return None
    
    def end_game(self, result):
        """Handle the end of the game by disabling buttons and showing a message."""
        if result == "Tie":
            self.status_label.config(text="It's a Tie!")
            messagebox.showinfo("Game Over", "It's a Tie!")
        else:
            self.status_label.config(text=f"{result} Wins!")
            messagebox.showinfo("Game Over", f"Player {result} wins!")
        
        # Disable all buttons
        for r in range(3):
            for c in range(3):
                self.buttons[r][c].config(state=tk.DISABLED)
    
    def reset_game(self):
        """Reset the game to its initial state."""
        self.board = [["" for _ in range(3)] for _ in range(3)]
        self.current_player = "X"
        self.status_label.config(text=f"{self.current_player}'s Turn")
        
        for r in range(3):
            for c in range(3):
                self.buttons[r][c].config(text="", state=tk.NORMAL)

def main():
    root = tk.Tk()
    game = TicTacToe(root)
    root.mainloop()

if __name__ == "__main__":
    main()
