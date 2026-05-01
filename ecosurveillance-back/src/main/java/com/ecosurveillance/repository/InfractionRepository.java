package com.ecosurveillance.repository;

import com.ecosurveillance.entity.Infraction;
import com.ecosurveillance.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import com.ecosurveillance.enums.StatusInfraction;

import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface InfractionRepository extends JpaRepository<Infraction, Long> {

    List<Infraction> findByEtudiant(User etudiant);
    long countByInfractionDateAfter(LocalDateTime date);
    List<Infraction> findByEtudiantAndInfractionDateAfter(User etudiant, LocalDateTime date);
    List<Infraction> findByStatus(StatusInfraction status);

    long countBy();
    @Query("SELECT i.status, COUNT(i) FROM Infraction i GROUP BY i.status")
    List<Object[]> countByStatus();

    @Query("""
    SELECT 
        CASE 
            WHEN :isDaily = true 
                THEN FUNCTION('DATE', i.infractionDate)
            ELSE FUNCTION('DATE_FORMAT', i.infractionDate, '%Y-%m')
        END,
        COUNT(i)
    FROM Infraction i
    WHERE i.infractionDate >= :startDate
    GROUP BY 
        CASE 
            WHEN :isDaily = true 
                THEN FUNCTION('DATE', i.infractionDate)
            ELSE FUNCTION('DATE_FORMAT', i.infractionDate, '%Y-%m')
        END
    ORDER BY 1
""")
    List<Object[]> evolutionFlexible(
            LocalDateTime startDate,
            boolean isDaily
    );
}