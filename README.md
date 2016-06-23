# Skribble Process #

Ths skribble process will take in the skribble json specification and create a flattened image.  The the process MUST accept in the id of 
the skribble to process.  The skribble process MUST complete the following validataion on the specification:

1. All assets requested to be included MUST exist in the media server  
2. All assets requested MUST match the __check__ field from the media service in the matching specification   
3. All assets that cannot overlap MUST NOT have points that intersect on the grid based on __type__ of asset  
4. For Effect, Sound and Background, there MUST NOT be more than one instance of that type  
5. Status MUST BE "PROCESSING"

The generated image MUST BE a png file that is web optimized.  Once the image is generated, the image is then POSTed back to the __api__ with the skribble id.
