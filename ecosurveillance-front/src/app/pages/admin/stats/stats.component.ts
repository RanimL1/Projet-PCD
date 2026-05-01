import { Component, OnInit, AfterViewInit, OnDestroy, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { Chart, registerables } from 'chart.js';
import { DashboardService } from '../../../services/dashboard.service';
import { AuthService } from '../../../services/auth.service';
import { forkJoin, Subscription } from 'rxjs';

Chart.register(...registerables);

@Component({
  selector: 'app-stats',
  standalone: true,
  imports: [CommonModule, RouterModule],
  templateUrl: './stats.component.html',
  styleUrls: ['./stats.component.css']
})
export class StatsComponent implements OnInit, AfterViewInit, OnDestroy {
  barChart: any;
  lineChart: any;
  currentUser: any = null;

  // MODIFICATION : période par défaut → 2M
  selectedPeriod: string = '2M';

  // Périodes disponibles affichées dans le template
  periods = [
    { value: '1M', label: '1 Mois' },
    { value: '2M', label: '2 Mois' },
    { value: '3M', label: '3 Mois' },
    { value: '6M', label: '6 Mois' }
  ];

  private dataSubscription?: Subscription;
  private statusData: any = null;
  private evolutionData: any[] = [];

  constructor(
    private dashboardService: DashboardService,
    private router: Router,
    private authService: AuthService,
    private cdr: ChangeDetectorRef
  ) {}

  ngOnInit(): void {
    this.currentUser = this.authService.getCurrentUser();
    this.loadStats();
  }

  ngAfterViewInit(): void {
    if (this.statusData) {
      this.renderAllCharts();
    }
  }

  ngOnDestroy(): void {
    if (this.dataSubscription) this.dataSubscription.unsubscribe();
    this.destroyCharts();
  }

  // ─── Chargement des données ───────────────────────────────────────────────

  loadStats(): void {
    this.dataSubscription = forkJoin({
      status: this.dashboardService.getInfractionsByStatus(),
      evolution: this.dashboardService.getInfractionsEvolution(this.selectedPeriod)
    }).subscribe({
      next: ({ status, evolution }) => {
        this.statusData = status;
        this.evolutionData = evolution;
        console.log('Evolution RAW:', JSON.stringify(evolution));
        this.cdr.detectChanges();
        this.renderAllCharts();
      },
      error: (err) => console.error('Erreur API :', err)
    });
  }

  // Appelé depuis le HTML : (click)="changePeriod('2M')"
  changePeriod(period: string): void {
    this.selectedPeriod = period;
    this.loadStats();
  }

  // ─── Rendu des graphiques ─────────────────────────────────────────────────

  private renderAllCharts(): void {
    setTimeout(() => {
      this.initBarChart();
      this.initLineChart();
    }, 100);
  }

  private initBarChart(): void {
    const canvas = document.getElementById('barChart') as HTMLCanvasElement;
    if (!canvas) return;
    if (this.barChart) this.barChart.destroy();

    this.barChart = new Chart(canvas, {
      type: 'bar',
      data: {
        labels: ['En attente', 'Terminée', 'En cours'],
        datasets: [{
          label: 'Infractions',
          data: [
            this.statusData?.en_attente ?? 0,
            this.statusData?.terminee   ?? 0,
            this.statusData?.en_cours   ?? 0
          ],
          backgroundColor: ['#4285F4', '#0F9D58', '#f59e0b'],
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
      }
    });
  }

  private initLineChart(): void {
    const canvas = document.getElementById('lineChart') as HTMLCanvasElement;
    if (!canvas) return;
    if (this.lineChart) this.lineChart.destroy();

    // Clés exactes du backend → "periode" et "total"
    const labels = this.evolutionData.map((item: any) =>
      item.periode ?? item.date ?? item.label ?? item.mois ?? ''
    );
    const values = this.evolutionData.map((item: any) =>
      Number(item.total ?? item.count ?? item.value ?? 0)
    );

    this.lineChart = new Chart(canvas, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Évolution des infractions',
          data: values,
          borderColor: '#4285F4',
          backgroundColor: 'rgba(66, 133, 244, 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 4,
          pointBackgroundColor: '#4285F4'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { precision: 0 } }
        }
      }
    });
  }

  private destroyCharts(): void {
    if (this.barChart) this.barChart.destroy();
    if (this.lineChart) this.lineChart.destroy();
  }

  onLogout(): void {
    localStorage.clear();
    this.router.navigate(['/login']);
  }
}
