import cv2
from cvzone.HandTrackingModule import HandDetector

if __name__ == "__main__":
    cam_x, cam_y = 640, 480

    cap = cv2.VideoCapture(0)
    cap.set(3, cam_x)
    cap.set(4, cam_y)

    detector = HandDetector(detectionCon=0.8, maxHands=1)

    while True:
        success, img = cap.read()
        
        img = cv2.flip(img, 1)
        hands, img = detector.findHands(img)
        if hands:
            print("detected")

        cv2.imshow("Image", img)
        key = cv2.waitKey(1)

        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
