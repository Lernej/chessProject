import cv2 as cv2
import numpy as np
import math

#return an array storing top left, top right, bottom right, bottom left in order
def orderVertices(border):
    pointSums = np.sum(border, axis=1)
    pointDiffs = np.diff(border, axis = 1)
    
    topLeft = border[np.argmin(pointSums)]
    bottomRight = border[np.argmax(pointSums)]
    
    topRight = border[np.argmin(pointDiffs)]
    bottomLeft = border[np.argmax(pointDiffs)]

    return np.array([topLeft, topRight, bottomRight, bottomLeft], dtype=np.float32)

def extractLines(lines):
    threshold_angle = 5 * (np.pi / 180) 
    lines_horizontal = []
    lines_vertical = []
    for line in lines:
        
        
        x1, y1, x2, y2 = line[0]
        
        # Calculate angle in radians
        angle = math.atan2(y2 - y1, x2 - x1)
        
        # Normalize angle to be between 0 and pi
        if angle < 0:
            angle += np.pi
            
        # Classify
        if angle < threshold_angle or abs(angle - np.pi) < threshold_angle:
            lines_horizontal.append(line)
        elif abs(angle - (np.pi / 2)) < threshold_angle:
            lines_vertical.append(line)
        
       
    return lines_horizontal, lines_vertical

img = cv2.imread('uploaded_test.jpg')

# Convert to grayscale
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Blur the image
blur = cv2.GaussianBlur(gray, (33,33), 0)

thresh = cv2.adaptiveThreshold(
    src = blur,
    maxValue = 255,
    adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    thresholdType=cv2.THRESH_BINARY,
    blockSize=23,
    C=2
)




cv2.imshow("Dilated", thresh)

contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)


height, width, _ = img.shape
quadrilaterals = []
image_vertices = np.array([
    [0, 0],
    [width - 1, 0],
    [width - 1, height - 1],
    [0, height - 1]
], dtype=np.float32)
print(image_vertices)

for c in contours:
    hull = cv2.convexHull(c)

    peri = cv2.arcLength(hull, True)
    approx = cv2.approxPolyDP(hull, 0.02 * peri, True)

    
    
    area = cv2.contourArea(approx)
    if area < 10000 or len(approx) != 4:
        continue
    
    reshaped = np.reshape(approx, (4, -1))
    reshaped = orderVertices(reshaped)
    if (np.array_equal(reshaped, image_vertices)):
        continue
    

    if len(approx) == 4 and cv2.isContourConvex(approx):
        quadrilaterals.append(reshaped)



if len(quadrilaterals) == 1:
    board = quadrilaterals[0]
    matrix = cv2.getPerspectiveTransform(board, image_vertices)
    
    refocused = cv2.warpPerspective(img, matrix, (width, height))
    cv2.imshow("Refocused", refocused)

cv2.imshow("Contour Image", img)
cv2.waitKey(0)
cv2.destroyAllWindows()