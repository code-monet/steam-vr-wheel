
import numpy as np

def clamp(x, m, M):
    return min(M, max(m, x))

class Rad(float):
    def __new__(cls, value):
        if isinstance(value, Deg):
            value = value / 180 * np.pi
        return super().__new__(cls, value)

class Deg(float):
    def __new__(cls, value):
        if isinstance(value, Rad):
            value = value / np.pi * 180
        return super().__new__(cls, value)

def bezier_curve(t, P0, P1, P2, P3):
    return (1-t)**3 * P0 + 3*(1-t)**2 * t * P1 + 3*(1-t) * t**2 * P2 + t**3 * P3

class Point:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

def print_matrix(matrix):
    l = []
    for i in range(3):
        ll = []
        for j in range(4):
            ll.append(matrix[j])
        l.append(ll)
    print(l)

def rotation_matrix(theta1, theta2, theta3):
    #https://programming-surgeon.com/en/euler-angle-python-en/
    c1 = np.cos(theta1 * np.pi / 180)
    s1 = np.sin(theta1 * np.pi / 180)
    c2 = np.cos(theta2 * np.pi / 180)
    s2 = np.sin(theta2 * np.pi / 180)
    c3 = np.cos(theta3 * np.pi / 180)
    s3 = np.sin(theta3 * np.pi / 180)

    return np.array([[c2*c3, -c2*s3, s2],
                         [c1*s3+c3*s1*s2, c1*c3-s1*s2*s3, -c2*s1],
                         [s1*s3-c1*c3*s2, c3*s1+c1*s2*s3, c1*c2]])
                         
def rotation_matrix_around_vec(theta, vec):
    theta = theta * np.pi / 180
    m = sqrt(vec[0]**2 + vec[1]**2 + vec[2]**2)
    ux = vec[0]/m
    uy = vec[1]/m
    uz = vec[2]/m
    s, c = sin(theta), cos(theta)

    return np.array([[c+ux**2*(1-c), ux*uy*(1-c)-uz*s, ux*uz*(1-c)+uy*s],
                    [uy*ux*(1-c)+uz*s, c+uy**2*(1-c), uy*uz*(1-c)-ux*s],
                    [uz*ux*(1-c)-uy*s, uz*uy*(1-c)+ux*s, c+uz**2*(1-c)]])