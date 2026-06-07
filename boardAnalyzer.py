import cv2 as cv
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

img = cv.imread('uploaded_test.jpg')

# Convert to grayscale
gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

# Blur the image
blur = cv.GaussianBlur(gray, (7,7), 0)

# Use thresh to create contrast between board and background
thresh = cv.adaptiveThreshold(
    blur,
    255,
    cv.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv.THRESH_BINARY,
    81,
    1
)

# Comment to show thresh image
# cv.imshow('Thresh', thresh)

# Find contours
contours, hierarchy = cv.findContours(thresh, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)

foundBorder = []

# Traverse each contour
for contour in contours:
    peri = cv.arcLength(contour, True)
    approx = cv.approxPolyDP(contour, 0.02 * peri, True)
    
    
    area = cv.contourArea(contour)
    # Skip small contours
    if area < 10000:
        continue
    
    # If we have four vertices (quadrilateral)
    if len(approx) == 4:
      
        x, y, w, h = cv.boundingRect(approx)
        img_h, img_w = img.shape[:2]
        margin = 10
        
        # Skip anything that might be the border of our photo
        if (
            x <= margin or
            y <= margin or
            x + w >= img_w - margin or
            y + h >= img_h - margin
        ):
            continue

        aspect_ratio = float(w) / h

        # Draw the contour
        cv.drawContours(img, [approx], -1, (0, 255, 0), 2)
        foundBorder.append(approx)


if len(foundBorder) == 1:
    border = foundBorder[0]
    border = border.reshape(4,2)
    
    orderedBorder = orderVertices(border)
    
    board_size = 800
    
    
    dst = np.array([
        [0,0],
        [board_size - 1, 0],
        [board_size - 1, board_size - 1],
        [0, board_size - 1]
    ], dtype=np.float32)

    # Warp onto the found border
    M = cv.getPerspectiveTransform(orderedBorder, dst)

    warped = cv.warpPerspective(img, M, (board_size, board_size))

    # Now we repeat to find inner board (8x8 grid)
    gray = cv.cvtColor(warped, cv.COLOR_BGR2GRAY)
    blur = cv.GaussianBlur(gray, (5,5), 0)
    
    cv.imshow('Blur', blur)

    edges = cv.Canny(blur, threshold1=10, threshold2=30)
    lines = cv.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=150, minLineLength=50, maxLineGap=100)

    horizontal, vertical = extractLines(lines)

    sorted_vertical = sorted(vertical, key=lambda line: line[0][0])
    merged_vertical = []

    for line in sorted_vertical:
        if not merged_vertical:
            merged_vertical.append(line)
        elif abs(line[0][0] - merged_vertical[-1][0][0]) > 25:
            merged_vertical.append(line)
    

    sorted_horizontal = sorted(horizontal, key=lambda line: line[0][1])
    merged_horizontal = []

    for line in sorted_horizontal:
        if not merged_horizontal:
            merged_horizontal.append(line)
        elif abs(line[0][1] - merged_horizontal[-1][0][1]) > 25:
            merged_horizontal.append(line)
    
    
    #reset here
    horizontal = merged_horizontal
    vertical = merged_vertical

    #now get the ys of the horizontal lines
    ys = []
    for line in horizontal:
        ys.append((line[0][1] + line[0][3]) / 2)
    
    diff = np.diff(ys)
    median = np.median(diff)
    evenlySpaced = []
    test = []
    for i, lineDiff in enumerate(diff):
        if abs(lineDiff - median) < 10:
            test.append(lineDiff)
            evenlySpaced.append(horizontal[i])
    
    horizontal = evenlySpaced
   
    #now get the ys of the horizontal lines
    xs = []
    for line in vertical:
        xs.append((line[0][0] + line[0][2]) / 2)
    
    diff = np.diff(xs)
    median = np.median(diff)
    evenlySpaced = []
    test = []
    for i, lineDiff in enumerate(diff):
        if abs(lineDiff - median) < 15:
            evenlySpaced.append(vertical[i])
    
    vertical = evenlySpaced
    
    print(len(vertical))
    print(len(horizontal))

    # Draw the lines
    if lines is not None:
        for line in vertical:
            x1, y1, x2, y2 = line[0]
            cv.line(warped, (x1, y1), (x2, y2), (0, 255, 0), 2)
        for line in horizontal:
            x1, y1, x2, y2 = line[0]
            cv.line(warped, (x1, y1), (x2, y2), (0, 255, 0), 2)
        

    
    
    cv.imshow('BoardView', warped)
    



# cv.imshow("Image", img)

cv.waitKey(0)
