package com.memoryseed.backend.domain.pet.repository;

import com.memoryseed.backend.domain.pet.entity.Pet;
import com.memoryseed.backend.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface PetRepository extends JpaRepository<Pet, Long> {
    Optional<Pet> findByUser(User user);
}