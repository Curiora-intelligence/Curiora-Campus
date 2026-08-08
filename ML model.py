from sklearn.linear_model import LinearRegression
import numpy as np,pickle
# --- ML MODEL SETUP ---
X_train = np.array([[0], [1], [2], [3]]) 
y_train = np.array([2, 5, 3, 7]) 
model = LinearRegression().fit(X_train, y_train)
with open("predict.pkl",'wb') as f:
    pickle.dump(model,f)

