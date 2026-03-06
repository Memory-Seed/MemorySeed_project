package com.memoryseed.backend.domain.pet.controller;

import com.memoryseed.backend.domain.pet.dto.CustomizationRequest;
import com.memoryseed.backend.domain.pet.dto.PetResponse;
import com.memoryseed.backend.domain.pet.service.PetService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/pet")
public class PetController {

    private final PetService petService;

    public PetController(PetService petService) {
        this.petService = petService;
    }

    @GetMapping
    public ResponseEntity<PetResponse> getPet(
            @RequestHeader("X-USER-ID") Long userId
    ) {
        return ResponseEntity.ok(petService.getPet(userId));
    }

    @PutMapping("/customization")
    public ResponseEntity<PetResponse> apply(
            @RequestHeader("X-USER-ID") Long userId,
            @RequestBody CustomizationRequest req
    ) {
        return ResponseEntity.ok(petService.applyCustomization(userId, req));
    }
}