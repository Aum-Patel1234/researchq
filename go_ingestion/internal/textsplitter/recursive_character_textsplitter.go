package textsplitter

/*
* RecursiveCharacterTextSplitter:
*
* seperators: ["\n\n", "\n", " ", ""]
 */

var seperators = [4]string{"\n\n", "\n", " ", ""}

type RecursiveCharacterTextSplitter struct {
	chunkSize    uint32
	chunkOverlap uint8
	fullString   string
}

func Split(text *RecursiveCharacterTextSplitter) {

}
