from inference import get_model
import supervision as sv
import cv2
import boardGrid



def detect_pieces(image_file):
	image = cv2.imread(image_file)

	# load a pre-trained rfdetr model
	model = get_model(model_id="chess-project-9lzcy/1")

	# run inference on our chosen image, image can be a url, a numpy array, a PIL image, etc.
	results = model.infer(image)[0]

	# load the results into the supervision Detections api
	detections = sv.Detections.from_inference(results)

	# create supervision annotators
	bounding_box_annotator = sv.BoxAnnotator()
	label_annotator = sv.LabelAnnotator()

	# annotate the image with our inference results
	annotated_image = bounding_box_annotator.annotate(
		scene=image, detections=detections)
	

	# display the image
	# sv.plot_image(annotated_image)

	square_piece_map = {}

	# Traverse detected pieces and create a map (square -> piece). The model
	# only reports colour, so class_name is "white_piece" or "black_piece" --
	# piece identity comes from the board state tracked in main.py.
	for xyxy, confidence, class_name in zip(detections.xyxy, detections.confidence, detections.data['class_name']):
		x_min, y_min, x_max, y_max = xyxy

		middle_x = (x_min + x_max) / 2
		middle_y = (y_min + y_max) / 2

		square_name = boardGrid.get_square_from_coordinates(middle_x, middle_y)

		if square_name in square_piece_map:
			print("An error may have occured, please examine results (detected two pieces in the same square)")
		else:
			square_piece_map[square_name] = class_name
	
	
	return square_piece_map

