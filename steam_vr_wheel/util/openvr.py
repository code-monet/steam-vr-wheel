
import openvr
from math import sin, cos

def check_result(result):
    if result:
        error_name = openvr.VROverlay().getOverlayErrorNameFromEnum(result)
        raise Exception("OpenVR Error:", error_name)

def initRotationMatrix(axis, angle, matrix=None):
    # angle in radians
    if matrix is None:
        matrix = openvr.HmdMatrix34_t()
    if axis==0:
        matrix.m[0][0] = 1.0
        matrix.m[0][1] = 0.0
        matrix.m[0][2] = 0.0
        matrix.m[0][3] = 0.0
        matrix.m[1][0] = 0.0
        matrix.m[1][1] = cos(angle)
        matrix.m[1][2] = -sin(angle)
        matrix.m[1][3] = 0.0
        matrix.m[2][0] = 0.0
        matrix.m[2][1] = sin(angle)
        matrix.m[2][2] = cos(angle)
        matrix.m[2][3] = 0.0
    elif axis==1:
        matrix.m[0][0] = cos(angle)
        matrix.m[0][1] = 0.0
        matrix.m[0][2] = sin(angle)
        matrix.m[0][3] = 0.0
        matrix.m[1][0] = 0.0
        matrix.m[1][1] = 1.0
        matrix.m[1][2] = 0.0
        matrix.m[1][3] = 0.0
        matrix.m[2][0] = -sin(angle)
        matrix.m[2][1] = 0.0
        matrix.m[2][2] = cos(angle)
        matrix.m[2][3] = 0.0
    elif axis == 2:
        matrix.m[0][0] = cos(angle)
        matrix.m[0][1] = -sin(angle)
        matrix.m[0][2] = 0.0
        matrix.m[0][3] = 0.0
        matrix.m[1][0] = sin(angle)
        matrix.m[1][1] = cos(angle)
        matrix.m[1][2] = 0.0
        matrix.m[1][3] = 0.0
        matrix.m[2][0] = 0.0
        matrix.m[2][1] = 0.0
        matrix.m[2][2] = 1.0
        matrix.m[2][3] = 0.0
    return matrix

def matMul33(a, b, result=None):
    if result is None:
        result = openvr.HmdMatrix34_t()
    for i in range(3):
        for j in range(3):
            result.m[i][j] = 0.0
            for k in range(3):
                result.m[i][j] += a.m[i][k] * b.m[k][j]
    result[0][3] = b[0][3]
    result[1][3] = b[1][3]
    result[2][3] = b[2][3]
    return result

def set_transform(tf, mat):
    for i in range(0, 3):
        for j in range(0, 4):
            tf[i][j] = mat[i][j]
