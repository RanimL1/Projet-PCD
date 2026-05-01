// package com.ecosurveillance.entity;

// import jakarta.persistence.Entity;
// import jakarta.persistence.GeneratedValue;
// import jakarta.persistence.ManyToOne;
// import lombok.Getter;
// import lombok.Setter;
// import jakarta.persistence.Id;

// @Entity
// @Getter
// @Setter
// public class Preuve {

//     @Id
//     @GeneratedValue
//     private Long id;

//     private String imageUrl;
//     private String videoUrl;

//     @ManyToOne
//     private Infraction infraction;
// }

package com.ecosurveillance.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.Setter;
import java.time.LocalDateTime;

import static java.time.LocalDateTime.*;

@Entity
@Table(name = "preuves")
@Getter
@Setter

public class Preuve {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String imageUrl;
    private String videoUrl;

    private LocalDateTime createdAt = now();

    @ManyToOne
    @JoinColumn(name = "infraction_id")
    private Infraction infraction;
}