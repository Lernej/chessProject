import cv2 as cv2
import numpy as np
import os
import pieceDetection

output_folder = "photos"

# Overall function to be called from the API. Return a map of square to piece.
def get_board_map(path):
    
    
    #return an array storing top left, top right, bottom right, bottom left in order
    def orderVertices(border):
        pointSums = np.sum(border, axis=1)
        pointDiffs = np.diff(border, axis = 1)
        
        topLeft = border[np.argmin(pointSums)]
        bottomRight = border[np.argmax(pointSums)]
        
        topRight = border[np.argmin(pointDiffs)]
        bottomLeft = border[np.argmax(pointDiffs)]

        return np.array([topLeft, topRight, bottomRight, bottomLeft], dtype=np.float32)

    # Check if two matrixes are approximately equal (will be used to filter out image edge contour)
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
    
    
    img = cv2.imread(path)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Blur the image
    blur = cv2.GaussianBlur(gray, (33,33), 0)

    thresh = cv2.adaptiveThreshold(
        src = blur,
        maxValue = 255,
        adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        thresholdType=cv2.THRESH_BINARY,
        blockSize=33,
        C=2
    )


    # cv2.imshow("Dilated", thresh)


    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # cv2.drawContours(img, contours, -1, (0, 255, 0), 2)

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
        x, y, w, h = cv2.boundingRect(approx)



        area = cv2.contourArea(approx)
        if area < 1000 or len(approx) != 4:
            continue
        if (w / h) < .95 or (w / h) > 1.05:
            continue



        
        reshaped = np.reshape(approx, (4, -1))
        reshaped = orderVertices(reshaped)
        if (np.array_equal(reshaped, image_vertices)):
            continue
        
        

        if len(approx) == 4 and not approxEqual(reshaped, image_vertices):
            quadrilaterals.append(reshaped)
            # cv2.drawContours(img, [approx], -1, (255, 0, 0), 2)

    # cv2.imshow("Image", img)
    # cv2.waitKey(0)

    
    # Assumes the first quadrilateral we find is the board
    if len(quadrilaterals) > 0:
        board = quadrilaterals[0]
        matrix = cv2.getPerspectiveTransform(board, image_vertices)
        
        refocused = cv2.warpPerspective(img, matrix, (width, height))

        gray = cv2.cvtColor(refocused, cv2.COLOR_BGR2GRAY)
        
        # cv2.imshow("Refocused", refocused)
        file_name = "board.jpg"
        full_path = os.path.join(output_folder, file_name)
        
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        success = cv2.imwrite(full_path, refocused)

        return pieceDetection.detect_pieces(f"{output_folder}/{file_name}")


    else:
        print("No board detected!")
        return {}




# get_board_map()
