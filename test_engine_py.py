import chess
from stockfish import Stockfish

# Point to the Stockfish executable in your project folder
STOCKFISH_PATH = "./stockfish-windows-x86-64-avx2.exe"  # Update filename to match yours

stockfish = Stockfish(path=STOCKFISH_PATH, depth=15)

# Initialize a standard chess board
board = chess.Board()

# Make a couple of opening moves
board.push_san("e4")
board.push_san("e5")

# Send the current board position (FEN) to Stockfish
stockfish.set_fen_position(board.fen())

# Get the top 3 best moves and position evaluation
top_moves = stockfish.get_top_moves(3)
evaluation = stockfish.get_evaluation()

print("Evaluation:", evaluation)
print("Top 3 Moves:", top_moves)