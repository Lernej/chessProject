import cv2 as cv2
import numpy as np
import math
import os
import pieceDetection

output_folder = "photos"

def analyze_photo():

    #return an array storing top left, top right, bottom right, bottom left in order
    def orderVertices(border):
        pointSums = np.sum(border, axis=1)
        pointDiffs = np.diff(border, axis = 1)
        
        topLeft = border[np.argmin(pointSums)]
        bottomRight = border[np.argmax(pointSums)]
        
        topRight = border[np.argmin(pointDiffs)]
        bottomLeft = border[np.argmax(pointDiffs)]

        return np.array([topLeft, topRight, bottomRight, bottomLeft], dtype=np.float32)

    #split lines into horizontal and vertical groups
    def extractLines(lines):
        threshold_angle =  2.5 * (np.pi / 180) 
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

    def mergeLines(lines, horizontal = False, vertical = False):
        if (horizontal):
            lines = sorted(lines, key = lambda line: line[0][1])
            cleaned = []
            for line in lines:
                if not cleaned:
                    cleaned.append(line)
                elif abs(cleaned[-1][0][1] - line[0][1]) > 20:
                    cleaned.append(line)
            return cleaned
        if (vertical):
            lines = sorted(lines, key = lambda line: line[0][0])
            cleaned = []
            for line in lines:
                if not cleaned:
                    cleaned.append(line)
                elif abs(cleaned[-1][0][0] - line[0][0]) > 20:
                    cleaned.append(line)
            return cleaned   
    def approxEqual(matrix1, matrix2):
        count = 0
        for i in range(len(matrix1)):
            for j in range(len(matrix1[0])):
                if abs(matrix1[i][j] - matrix2[i][j]) > 10:
                    continue
                else:
                    count += 1
                    break
        return count == len(matrix1)
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




    # cv2.imshow("Dilated", thresh)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)


    height, width, _ = img.shape
    quadrilaterals = []
    image_vertices = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype=np.float32)


    for c in contours:
        hull = cv2.convexHull(c)

        peri = cv2.arcLength(hull, True)
        approx = cv2.approxPolyDP(hull, 0.02 * peri, True)

    

        
        area = cv2.contourArea(approx)
        if area < 1000 or len(approx) != 4:
            continue
        
        reshaped = np.reshape(approx, (4, -1))
        reshaped = orderVertices(reshaped)
        if (np.array_equal(reshaped, image_vertices)):
            continue
        
        print(len(approx))
        

        if len(approx) == 4 and not approxEqual(reshaped, image_vertices):
            quadrilaterals.append(reshaped)



    if len(quadrilaterals) > 0:
        board = quadrilaterals[0]
        matrix = cv2.getPerspectiveTransform(board, image_vertices)
        
        refocused = cv2.warpPerspective(img, matrix, (width, height))

        gray = cv2.cvtColor(refocused, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), 0)

        clahe = cv2.createCLAHE(clipLimit = 2.0, tileGridSize=(8,8))

        

        cl_img = clahe.apply(blur)

        # cv2.imshow("CLAHE", cl_img)

        edges = cv2.Canny(cl_img, 30, 100)

        # cv2.imshow("edges", edges)

        # 4. Extract straight lines using Probabilistic Hough Transform
        lines = cv2.HoughLinesP(
            edges, 
            rho=1, 
            theta=np.pi/180, 
            threshold=65, 
            minLineLength=400, 
            maxLineGap=100
        )

        
        # cv2.imshow("Refocused", refocused)
        file_name = "board.jpg"
        full_path = os.path.join(output_folder, file_name)
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        success = cv2.imwrite(full_path, refocused)
        
        pieceDetection.detect_pieces(f"{output_folder}/{file_name}")


    else:
        print("No board detected!")



# # cv2.imshow("Image", img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()