import cv2 as cv



img = cv.imread('uploaded_test.jpg')

gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
blur = cv.GaussianBlur(gray, (7,7), 0)

thresh = cv.adaptiveThreshold(
    blur,
    255,
    cv.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv.THRESH_BINARY,
    81,
    1
)

cv.imshow('Thresh', thresh)

contours, hierarchy = cv.findContours(thresh, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)

contours = sorted(contours, key = cv.contourArea, reverse = True)

for contour in contours:
    peri = cv.arcLength(contour, True)
    approx = cv.approxPolyDP(contour, 0.02 * peri, True)
    
    
    area = cv.contourArea(contour)
    if area < 10000:
        continue
 
    if len(approx) == 4:
      
        x, y, w, h = cv.boundingRect(approx)
        img_h, img_w = img.shape[:2]
        margin = 10
        if (
            x <= margin or
            y <= margin or
            x + w >= img_w - margin or
            y + h >= img_h - margin
        ):
            continue

        aspect_ratio = float(w) / h
        
        cv.drawContours(img, [approx], -1, (0, 255, 0), 2)



cv.imshow("Image", img)

cv.waitKey(0)
