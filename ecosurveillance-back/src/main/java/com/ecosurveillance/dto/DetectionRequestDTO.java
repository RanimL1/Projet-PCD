// package com.ecosurveillance.dto;

// import lombok.Data;

// @Data
// public class DetectionRequestDTO {
//     private String type;           // "littering"
//     private Integer trackId;       // ID DeepSORT
//     private String capturePath;    // Chemin de l'image
//     private String bboxCoordinates; // "[x1,y1,x2,y2]"
//     private Long userId;           // Optionnel si identifié
// }
package com.ecosurveillance.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import org.springframework.web.multipart.MultipartFile;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class DetectionRequestDTO {
    private String type;
    private String trackId;
    private String bboxCoordinates;
    private String userId;
    private MultipartFile photo;
    private MultipartFile video;
}