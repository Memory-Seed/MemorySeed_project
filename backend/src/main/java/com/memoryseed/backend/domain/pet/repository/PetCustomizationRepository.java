package com.memoryseed.backend.domain.pet.repository;

import com.memoryseed.backend.domain.pet.entity.PetCustomization;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PetCustomizationRepository extends JpaRepository<PetCustomization, Long> {
}