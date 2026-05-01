import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  loginForm: FormGroup;
  errorMessage: string = '';
  isLoading: boolean = false;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {
    this.loginForm = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]]
    });
  }

//   onSubmit(): void {
//     if (this.loginForm.valid) {
//       this.isLoading = true;
//       this.errorMessage = '';

//       setTimeout(() => {
//         const credentials = this.loginForm.value;

//         if (credentials.email === 'admin@ecosurveillance.com' && credentials.password === 'admin123') {
//           localStorage.setItem('token', 'fake-jwt-token');
//           localStorage.setItem('role', 'ADMIN');
//           localStorage.setItem('user', JSON.stringify({
//             nom: 'Admin',
//             role: 'ADMIN',
//             email: credentials.email
//           }));
//           this.router.navigate(['/admin/dashboard']);
//         } else if (credentials.email === 'etudiant@ecosurveillance.com' && credentials.password === 'etudiant123') {
//           localStorage.setItem('token', 'fake-jwt-token');
//           localStorage.setItem('role', 'ETUDIANT');
//           localStorage.setItem('user', JSON.stringify({
//             nom: 'Foulen Ben Foulen',
//             role: 'ETUDIANT',
//             matricule: 'ETU001',
//             email: credentials.email
//           }));
//           this.router.navigate(['/user/my-infractions']);
//         } else {
//           this.errorMessage = 'Email ou mot de passe incorrect';
//         }

//         this.isLoading = false;
//       }, 1000);
//     }
//   }
// }
  onSubmit(): void {
  if (this.loginForm.valid) {
    this.isLoading = true;
    this.errorMessage = '';

    this.authService.login(this.loginForm.value).subscribe({
      next: (res) => {
        this.isLoading = false;
        if (res.role === 'ADMIN') {
          this.router.navigate(['/admin/dashboard']);
        } else {
          this.router.navigate(['/user/my-infractions']);
        }
      },
      error: () => {
        this.isLoading = false;
        this.errorMessage = 'Email ou mot de passe incorrect';
      }
    });
  }
}
}
