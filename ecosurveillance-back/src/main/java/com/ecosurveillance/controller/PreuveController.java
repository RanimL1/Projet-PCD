package com.ecosurveillance.controller;

import com.ecosurveillance.entity.Infraction;
import com.ecosurveillance.repository.InfractionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import jakarta.servlet.http.HttpServletRequest;

import java.io.IOException;
import java.nio.file.*;
import java.util.*;

@RestController
@RequestMapping("/api/preuves")
@CrossOrigin(origins = "*")
@RequiredArgsConstructor
public class PreuveController {

    private final InfractionRepository infractionRepository;
    
    @Value("${preuves.storage.path}")
    private String storagePath;

    @GetMapping("/infraction/{infractionId}")
    public ResponseEntity<List<Map<String, String>>> getPreuvesByInfraction(@PathVariable Long infractionId) {
        Optional<Infraction> infractionOpt = infractionRepository.findById(infractionId);
        
        if (infractionOpt.isEmpty()) {
            return ResponseEntity.ok(new ArrayList<>());
        }
        
        Infraction infraction = infractionOpt.get();
        List<Map<String, String>> result = new ArrayList<>();
        
        String preuveUrl = infraction.getPreuveUrl();
        if (preuveUrl != null && !preuveUrl.isEmpty()) {
            Map<String, String> preuveMap = new HashMap<>();
            preuveMap.put("id", String.valueOf(infraction.getId()));
            preuveMap.put("type", "IMAGE");
            preuveMap.put("photoUrl", "/api/preuves/media/" + preuveUrl);
            preuveMap.put("videoUrl", "");
            result.add(preuveMap);
        }
        
        return ResponseEntity.ok(result);
    }

    @GetMapping("/media/**")
    public ResponseEntity<Resource> servirMedia(HttpServletRequest request) throws IOException {
        // Exemple: "alertes/alerte_ID1_20260324_163200.jpg"
        String cheminRelatif = request.getRequestURI().replaceFirst("/api/preuves/media/", "");
        
        // Combine: C:/Users/GIGABYTE/Desktop/liaison/detection_main/detection_aoi + alertes/alerte_ID1_20260324_163200.jpg
        Path filePath = Paths.get(storagePath, cheminRelatif).normalize();
        
        System.out.println("🔍 Recherche fichier: " + filePath.toString()); // Pour voir le chemin dans la console
        
        Resource resource = new UrlResource(filePath.toUri());

        if (!resource.exists()) {
            System.out.println("❌ Fichier non trouvé: " + filePath.toString());
            return ResponseEntity.notFound().build();
        }

        String contentType = Files.probeContentType(filePath);
        if (contentType == null) contentType = "image/jpeg";

        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(contentType))
                .header("Content-Disposition", "inline")
                .body(resource);
    }
}