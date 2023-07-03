import matplotlib.pyplot as plt
import numpy as np

p = [1, 0.99, 0.98, 0.97, 0.75, 0.5]
dense = [0, 0, 16, 16, 160, 40]
normal = [360, 360, 344, 344, 200, 320]

X = np.arange(len(p))
plt.bar(X - 0.2, dense, 0.4, label = 'Dense')
plt.bar(X + 0.2, normal, 0.4, label = 'Without Dense')
plt.xticks(X, list(map(str, p)))
plt.ylabel('Number of Bits')
plt.xlabel('p')
plt.title('Number of Bits Sent with and without Dense Coding')
plt.legend()
plt.show()